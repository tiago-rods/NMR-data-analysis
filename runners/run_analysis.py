"""
Statistical Analysis Runner.

Orchestrates the full pipeline: Load → Calculate → Persist.

  1. [Load]      StatsCalculator fetches (tool vs Gold Standard) pairs from the database.
  2. [Calculate] StatsEngine calculates metrics at 3 levels of granularity.
  3. [Persist]   AnalysisSeeder upserts results into the analytical tables.

Usage:
    python runners/run_analysis.py
    python runners/run_analysis.py --tool ASICS
    python runners/run_analysis.py --tool nmRanalysis --log-level DEBUG
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add the project root to sys.path so absolute imports work correctly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db_manager import DataBaseManager
from database.seeders.analysis_seeder import AnalysisSeeder
from src.analysis.stats_calculator import StatsCalculator
from src.analysis.stats_engine import StatsEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the analysis runner.

    Returns:
        argparse.Namespace: Parsed arguments with ``tool`` and ``log_level`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "NMR statistical analysis pipeline.\n"
            "Calculates Pearson, Spearman, Bias, MSE, MAPE and Coverage "
            "comparing tools against the Gold Standard."
        )
    )
    parser.add_argument(
        "--tool",
        type=str,
        default=None,
        help=(
            "Name of the tool to analyse (e.g. ASICS, nmRanalysis, MagMet). "
            "If omitted, all tools are analysed."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


def run(tool_name: Optional[str] = None) -> None:
    """Executes the full statistical analysis pipeline.

    Args:
        tool_name (Optional[str]): Filter by a specific tool name; ``None`` runs all tools.
    """
    # ── 1. Load (Repository) ────────────────────────────────────────────────
    logger.info("=== STEP 1/3: Loading data from the database ===")
    db = DataBaseManager()
    calculator = StatsCalculator(db)

    observations = calculator.fetch_paired_data(tool_name=tool_name)

    if not observations:
        logger.warning(
            "No observations found%s. "
            "Please verify that the data has been ingested correctly.",
            f" for tool '{tool_name}'" if tool_name else "",
        )
        return

    logger.info("%d (tool vs GS) pairs loaded.", len(observations))

    # ── 2. Calculate (Strategy) ─────────────────────────────────────────────
    logger.info("=== STEP 2/3: Calculating metrics ===")
    engine = StatsEngine()
    counts = calculator.fetch_all_experiment_counts()
    metabolite_counts = calculator.fetch_all_metabolite_counts()
    results = engine.calculate_all(observations, counts, metabolite_counts)
    logger.info(
        "Metrics calculated successfully (%d spectra, %d metabolites, %d tools).",
        len(results[0]),
        len(results[1]),
        len(results[2]),
    )

    # ── 3. Persist (AnalysisSeeder) ─────────────────────────────────────────
    logger.info("=== STEP 3/3: Persisting results ===")
    seeder = AnalysisSeeder()
    seeder.seed(results)

    logger.info("=== Pipeline completed successfully. ===")


def main() -> None:
    """Entry point: parses CLI arguments and delegates to ``run()``."""
    args = parse_args()
    logging.getLogger().setLevel(args.log_level)
    run(tool_name=args.tool)


if __name__ == "__main__":
    main()
