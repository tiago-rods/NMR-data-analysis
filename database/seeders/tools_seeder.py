import os
import sys
from pathlib import Path

# Add project root to sys.path at the very top
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
from database.seeders.factory_seeder import FactorySeeder


class ToolsSeeder(FactorySeeder):
    """
    Seeder to manually import tool metadata (Name, Version, Technology, Avg Time)
    from `data/Metadata/metadata_tools.csv` into Supabase.
    """

    def seed(self, csv_path: Path | None = None) -> None:
        if csv_path is None:
            csv_path = Path("data/Metadata/metadata_tools.csv")

        if not csv_path.exists():
            print(f"Error: metadata file not found at {csv_path}")
            return

        print(f"\n--- Seeding Tools from {csv_path.name} ---")

        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Clean column names (strip spaces, remove trailing empty columns if any)
        df.columns = [col.strip() for col in df.columns]
        
        # Standardize column names (mapping both PT and EN variants)
        column_mapping = {
            "Ferramenta": "nome",
            "tool": "nome",
            "nome": "nome",
            "versão": "versao",
            "version": "versao",
            "versao": "versao",
            "tecnologia": "tecnologia",
            "technology": "tecnologia",
            "tech": "tecnologia",
            "tempo médio por espectro(s)": "tempo_medio_processamento",
            "tempo_medio_processamento": "tempo_medio_processamento",
            "tempo_medio": "tempo_medio_processamento",
            "tempo": "tempo_medio_processamento",
            "processing_time": "tempo_medio_processamento",
            "time": "tempo_medio_processamento",
        }

        # Rename matching columns
        renamed_cols = {}
        for col in df.columns:
            for key, val in column_mapping.items():
                if key.lower() in col.lower():
                    renamed_cols[col] = val
                    break
        df = df.rename(columns=renamed_cols)

        # Drop columns not mapped
        valid_cols = {"nome", "versao", "tecnologia", "tempo_medio_processamento"}
        df = df[[col for col in df.columns if col in valid_cols]]

        # Drop completely empty rows or rows without tool name
        df = df.dropna(subset=["nome"])
        
        records = []
        for _, row in df.iterrows():
            nome = str(row["nome"]).strip()
            if not nome:
                continue

            # Parse version, fallback to v1.0.0 if NaN/empty
            versao = row.get("versao")
            if pd.isna(versao) or str(versao).strip().lower() in ("nan", "null", ""):
                versao = "v1.0.0"
            else:
                versao = str(versao).strip()

            # Parse technology
            tecnologia = str(row.get("tecnologia", "Unknown")).strip()
            if not tecnologia or tecnologia.lower() in ("nan", "null"):
                tecnologia = "Unknown"

            # Parse processing time
            tempo = row.get("tempo_medio_processamento")
            try:
                tempo = float(tempo)
                if pd.isna(tempo) or tempo <= 0:
                    tempo = 1.0  # Default to 1.0 if not positive or missing, to satisfy DB constraint > 0
            except (ValueError, TypeError):
                tempo = 1.0

            data = {
                "nome": nome,
                "versao": versao,
                "tecnologia": tecnologia,
                "tempo_medio_processamento": tempo
            }
            records.append(data)

        print(f"Parsed {len(records)} tool definitions from CSV:")
        for r in records:
            print(f"  - {r['nome']} ({r['versao']}) [{r['tecnologia']}] -> {r['tempo_medio_processamento']}s")

        # Upsert records into public.ferramenta
        for record in records:
            try:
                self.supabase.table("ferramenta").upsert(
                    record, on_conflict="nome,versao,tecnologia"
                ).execute()
                print(f"Upserted: {record['nome']} ({record['versao']}) [{record['tecnologia']}]")
            except Exception as e:
                print(f"Error upserting tool {record['nome']}: {e}")
                raise

        print("Tools seeding completed successfully!")


if __name__ == "__main__":
    seeder = ToolsSeeder()
    seeder.run()
