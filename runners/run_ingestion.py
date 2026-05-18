"""
Runner de Ingestão — Sprint 2.

Extrai o ponto de entrada do ExperimentSeeder para um script independente,
mantendo o padrão de runners individuais do projeto.

Uso:
    python runners/run_ingestion.py
    python runners/run_ingestion.py --dir data/processed/formatted/Complete
"""

import sys
import argparse
import logging
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para importações absolutas funcionarem
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.seeders.tools_seeder import ToolsSeeder
from database.seeders.experiment_seeder import ExperimentSeeder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingere CSVs processados no Supabase (Sprint 2)."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("data/processed/formatted/Complete"),
        help="Diretório com os CSVs formatados (padrão: data/processed/formatted/Complete)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("Iniciando semeadura de ferramentas manuais...")
    tools_seeder = ToolsSeeder()
    tools_seeder.run()

    logger.info("Iniciando ingestão em: %s", args.dir)
    seeder = ExperimentSeeder()
    seeder.seed(input_dir=args.dir)
    logger.info("Ingestão concluída.")


if __name__ == "__main__":
    main()
