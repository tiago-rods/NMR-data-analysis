"""
Ingestion Runner.

Exposes the ExperimentSeeder entry point as a standalone script,
following the project's convention of individual runner scripts.

Usage:
    python runners/run_ingestion.py
    python runners/run_ingestion.py --dir data/processed/formatted/Complete
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the project root to sys.path so absolute imports work correctly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.seeders.tools_seeder import ToolsSeeder
from database.seeders.experiment_seeder import ExperimentSeeder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the ingestion runner.

    Returns:
        argparse.Namespace: Parsed arguments with a ``dir`` attribute pointing
        to the directory containing formatted CSV files.
    """
    parser = argparse.ArgumentParser(
        description="Ingests processed CSVs into Supabase."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("data/processed/formatted/Complete"),
        help="Directory containing formatted CSVs (default: data/processed/formatted/Complete)",
    )
    return parser.parse_args()


def run(input_dir: Path) -> None:
    """Seeds tools metadata and ingests experiment CSV files into the database.

    Args:
        input_dir (Path): Directory containing formatted CSVs.
    """
    logger.info("Starting tools metadata seeding...")
    tools_seeder = ToolsSeeder()
    tools_seeder.run()

    logger.info("Starting ingestion from: %s", input_dir)
    seeder = ExperimentSeeder()
    seeder.seed(input_dir=input_dir)
    logger.info("Ingestion completed.")


def main() -> None:
    """Entry point: parses arguments and delegates to run()."""
    args = parse_args()
    run(input_dir=args.dir)


if __name__ == "__main__":
    main()
