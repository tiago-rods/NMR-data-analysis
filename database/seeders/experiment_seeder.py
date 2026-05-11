import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    Client = None

from src.ingestion.metadata_extractor import MetadataExtractor
from src.ingestion.csv_to_jsonb import convert_wide_to_jsonb

class ExperimentSeeder:
    """
    Orchestrates the ingestion of processed CSV data into Supabase.
    Handles Instrument and Experiment registration before calling ingestion procedures.
    """
    def __init__(self):
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        
        self.supabase: Client = create_client(url, key)
        self.extractor = MetadataExtractor()

    def get_or_create_instrument(self, frequency: float, fabricant: str) -> int:
        """Ensures the instrument exists and returns its ID."""
        data = {"frequencia": frequency, "fabricante": fabricant}
        # Try to find existing
        res = self.supabase.table('instrumentos').select('id_instrumento')\
            .eq('frequencia', frequency).eq('fabricante', fabricant).execute()
        
        if res.data:
            return res.data[0]['id_instrumento']
        
        # Create new
        res = self.supabase.table('instrumentos').insert(data).execute()
        return res.data[0]['id_instrumento']

    def seed_experiments_from_columns(self, columns, instrument_id, biofluid):
        """Registers all spectra names as experiments in the database."""
        for col in columns:
            if col == 'metabolite' or col == 'Sample': continue
            
            data = {
                "fk_instrumento": instrument_id,
                "biofluido": biofluid,
                "espectro": str(col)
            }
            
            # Upsert experiment by spectrum name (assuming unique constraint exists or using select)
            try:
                self.supabase.table('experimento').upsert(data, on_conflict='espectro').execute()
            except Exception as e:
                print(f"Error seeding experiment {col}: {e}")

    def ingest_file(self, file_path: Path):
        """Processes a single CSV file and ingests its contents."""
        print(f"\n--- Ingesting: {file_path.name} ---")
        
        # 1. Extract Metadata
        meta = self.extractor.extract(str(file_path))
        
        # 2. Get/Create Instrument
        inst_id = self.get_or_create_instrument(meta.frequencia, meta.fornecedor)
        
        # 3. Read CSV
        df = pd.read_csv(file_path)
        
        # 4. Seed Experiments
        self.seed_experiments_from_columns(df.columns, inst_id, meta.biofluido)
        
        # 5. Convert to JSONB
        json_data = convert_wide_to_jsonb(df)
        
        # 6. Call Procedure for each spectrum
        is_gold_std = "LNBioGS" in file_path.name
        
        for spectrum, json_str in json_data.items():
            try:
                if is_gold_std:
                    print(f"  Ingesting GS for {spectrum}...")
                    self.supabase.rpc('ingest_gold_standard', {
                        'p_espectro_name': spectrum,
                        'p_json_data': json_str
                    }).execute()
                else:
                    print(f"  Ingesting Results for {spectrum} ({meta.ferramenta})...")
                    self.supabase.rpc('ingest_experiment_results', {
                        'p_espectro_name': spectrum,
                        'p_tool_name': meta.ferramenta,
                        'p_tool_version': meta.versao,
                        'p_tool_tech': meta.tecnologia,
                        'p_json_data': json_str
                    }).execute()
            except Exception as e:
                print(f"  Error ingesting spectrum {spectrum}: {e}")

    def run(self):
        input_dir = Path("data/processed/formatted/Complete")
        if not input_dir.exists():
            print(f"Directory {input_dir} not found.")
            return

        all_files = list(input_dir.glob("*.csv"))
        
        # Separate files to process Tool files first (to create experiments) and GS files last
        gs_files = [f for f in all_files if "LNBioGS" in f.name]
        tool_files = [f for f in all_files if "LNBioGS" not in f.name]
        
        print(f"Found {len(tool_files)} tool files and {len(gs_files)} Gold Standard files.")
        
        # 1. Process Tool Files (Seeds instruments and experiments)
        for file in tool_files:
            print(f"\n--- Ingesting Tool File: {file.name} ---")
            meta = self.extractor.extract(str(file))
            if not meta:
                print(f"Warning: Could not extract metadata from {file.name}. Skipping.")
                continue
                
            inst_id = self.get_or_create_instrument(meta.frequencia, meta.fabricante)
            df = pd.read_csv(file)
            self.seed_experiments_from_columns(df.columns, inst_id, meta.biofluido)
            
            json_data = convert_wide_to_jsonb(df)
            
            # Fetch the latest tool version from DB, default to 'v1.0.0'
            tool_version = "v1.0.0"
            try:
                version_res = self.supabase.table('ferramenta').select('versao')\
                    .eq('nome', meta.ferramenta).eq('tecnologia', meta.tecnologia)\
                    .order('versao', desc=True).limit(1).execute()
                if version_res.data:
                    tool_version = version_res.data[0]['versao']
            except Exception as e:
                print(f"Warning: Could not fetch version for {meta.ferramenta}, using {tool_version}.")
            
            for spectrum, json_str in json_data.items():
                try:
                    self.supabase.rpc('ingest_experiment_results', {
                        'p_espectro_name': spectrum,
                        'p_tool_name': meta.ferramenta,
                        'p_tool_version': tool_version,
                        'p_tool_tech': meta.tecnologia,
                        'p_json_data': json_str
                    }).execute()
                except Exception as e:
                    print(f"  Error ingesting spectrum {spectrum} for tool {meta.ferramenta}: {e}")

        # 2. Process Gold Standard Files
        for file in gs_files:
            print(f"\n--- Ingesting Gold Standard: {file.name} ---")
            df = pd.read_csv(file)
            json_data = convert_wide_to_jsonb(df)
            
            for spectrum, json_str in json_data.items():
                try:
                    self.supabase.rpc('ingest_gold_standard', {
                        'p_espectro_name': spectrum,
                        'p_json_data': json_str
                    }).execute()
                except Exception as e:
                    print(f"  Error ingesting GS spectrum {spectrum}: {e}")

if __name__ == "__main__":
    seeder = ExperimentSeeder()
    seeder.run()
