import json
import pandas as pd
from pathlib import Path

from database.seeders.factory_seeder import FactorySeeder
from src.ingestion.metadata_extractor import MetadataExtractor
from src.ingestion.csv_to_jsonb import convert_wide_to_jsonb


class ExperimentSeeder(FactorySeeder):
    """
    Orquestra a ingestão de CSVs processados no Supabase.
    Registra Instrumentos e Experimentos antes de chamar as stored procedures.
    Herda conexão e padrão de FactorySeeder.
    """

    def __init__(self):
        super().__init__()
        self.extractor = MetadataExtractor()

    # ── Contrato FactorySeeder ────────────────────────────────────────────────

    def seed(self, input_dir: Path | None = None) -> None:
        """Ponto de entrada: ingere todos os CSVs do diretório."""
        self._ingest_directory(input_dir or Path("data/processed/formatted/Complete"))

    # ── Helpers públicos ─────────────────────────────────────────────────────

    def get_or_create_instrument(self, frequency: float, fabricant: str) -> int:
        """Garante que o instrumento existe e retorna seu ID."""
        res = (
            self.supabase.table("instrumentos")
            .select("id_instrumento")
            .eq("frequencia", frequency)
            .eq("fabricante", fabricant)
            .execute()
        )

        if res.data:
            return res.data[0]["id_instrumento"]

        res = self.supabase.table("instrumentos").insert(
            {"frequencia": frequency, "fabricante": fabricant}
        ).execute()
        return res.data[0]["id_instrumento"]

    def seed_experiments_from_columns(
        self, columns, instrument_id: int, biofluid: str
    ) -> None:
        """Registra todos os nomes de espectro como experimentos no banco."""
        for col in columns:
            col_str = str(col)
            if col_str.lower() in ("metabolite", "sample", "id") or col_str.startswith("Unnamed:"):
                continue

            data = {
                "fk_instrumento": instrument_id,
                "biofluido": biofluid,
                "espectro": str(col),
            }

            try:
                self.supabase.table("experimento").upsert(
                    data, on_conflict="espectro"
                ).execute()
            except Exception as e:
                print(f"Erro ao registrar experimento {col}: {e}")

    # ── Lógica de ingestão ────────────────────────────────────────────────────

    def _ingest_directory(self, input_dir: Path) -> None:
        if not input_dir.exists():
            print(f"Diretório {input_dir} não encontrado.")
            return

        all_files = list(input_dir.glob("*.csv"))
        gs_files = [f for f in all_files if "LNBioGS" in f.name]
        tool_files = [f for f in all_files if "LNBioGS" not in f.name]

        print(
            f"Encontrados {len(tool_files)} arquivos de ferramenta"
            f" e {len(gs_files)} arquivos Gold Standard."
        )

        # 1. Ferramentas primeiro (cria experimentos e instrumentos)
        for file in tool_files:
            self._ingest_tool_file(file)

        # 2. Gold Standard por último (experimentos já existem)
        for file in gs_files:
            self._ingest_gs_file(file)

    def _ingest_tool_file(self, file: Path) -> None:
        print(f"\n--- Ingerindo Ferramenta: {file.name} ---")
        meta = self.extractor.extract(str(file))

        if not meta:
            print(f"  Aviso: metadados não encontrados em {file.name}. Pulando.")
            return

        inst_id = self.get_or_create_instrument(meta.frequencia, meta.fabricante)
        df = pd.read_csv(file)
        self.seed_experiments_from_columns(df.columns, inst_id, meta.biofluido)

        # Resolve versão da ferramenta
        try:
            version_res = (
                self.supabase.table("ferramenta")
                .select("versao")
                .eq("nome", meta.ferramenta)
                .eq("tecnologia", meta.tecnologia)
                .order("versao", desc=True)
                .limit(1)
                .execute()
            )
            if version_res.data:
                tool_version = version_res.data[0]["versao"]
                print(f"  Ferramenta '{meta.ferramenta}' ({meta.tecnologia}) resolvida com sucesso para a versão '{tool_version}'.")
            else:
                raise ValueError(
                    f"A ferramenta '{meta.ferramenta}' com tecnologia '{meta.tecnologia}' não foi encontrada "
                    f"na tabela public.ferramenta. Por favor, registre-a manualmente no arquivo "
                    f"'data/Metadata/metadata_tools.csv' e rode o ToolsSeeder antes de prosseguir com a ingestão."
                )
        except Exception as e:
            print(f"  Erro crítico ao validar ferramenta '{meta.ferramenta}' ({meta.tecnologia}): {e}")
            raise


        json_data = convert_wide_to_jsonb(df)

        for spectrum, json_str in json_data.items():
            try:
                self.supabase.rpc(
                    "ingest_experiment_results",
                    {
                        "p_espectro_name": spectrum,
                        "p_tool_name": meta.ferramenta,
                        "p_tool_version": tool_version,
                        "p_tool_tech": meta.tecnologia,
                        "p_json_data": json.loads(json_str),
                    },
                ).execute()
            except Exception as e:
                print(f"  Erro ao ingerir espectro {spectrum} ({meta.ferramenta}): {e}")

    def _ingest_gs_file(self, file: Path) -> None:
        print(f"\n--- Ingerindo Gold Standard: {file.name} ---")
        df = pd.read_csv(file)
        json_data = convert_wide_to_jsonb(df)

        for spectrum, json_str in json_data.items():
            try:
                self.supabase.rpc(
                    "ingest_gold_standard",
                    {"p_espectro_name": spectrum, "p_json_data": json.loads(json_str)},
                ).execute()
            except Exception as e:
                print(f"  Erro ao ingerir GS espectro {spectrum}: {e}")


if __name__ == "__main__":
    seeder = ExperimentSeeder()
    seeder.run()
