import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_standardize() -> None:
    """Executes the Gold Standard standardization pipeline."""
    logger.info("Executing: Gold Standard Standardization")
    from Scripts.standardize_gold_standard import main as standardize_main
    standardize_main()

def run_ingestion(input_dir: str) -> None:
    """Executes the ingestion pipeline.

    Args:
        input_dir (str): Directory containing formatted CSVs.
    """
    logger.info("Executing: Data Ingestion from %s", input_dir)
    from runners.run_ingestion import run as ingest_run
    ingest_run(Path(input_dir))

def run_analysis(tool: Optional[str] = None) -> None:
    """Executes the statistical analysis pipeline.

    Args:
        tool (Optional[str]): Tool name to filter by, or None for all.
    """
    logger.info("Executing: Statistical Analysis (Tool: %s)", tool or "All")
    from runners.run_analysis import run as analyze_run
    analyze_run(tool_name=tool)

def run_plots() -> None:
    """Executes the plot generation pipeline."""
    logger.info("Executing: Plot Generation")
    from generate_plots import main as plot_main
    plot_main()

def main() -> None:
    """Main entry point for the Unified CLI."""
    parser = argparse.ArgumentParser(
        description="Unified CLI for NMR Data Analysis Pipeline",
        epilog="Example usage: python cli.py ingest --dir data/processed/formatted/Complete"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: standardize
    subparsers.add_parser(
        "standardize", 
        help="Standardize the Gold Standard excel file into CSV."
    )

    # Command: ingest
    parser_ingest = subparsers.add_parser(
        "ingest", 
        help="Ingest formatted CSVs into the Supabase database."
    )
    parser_ingest.add_argument(
        "--dir", 
        type=str, 
        default="data/processed/formatted/Complete",
        help="Directory containing the formatted CSVs."
    )

    # Command: analyze
    parser_analyze = subparsers.add_parser(
        "analyze", 
        help="Calculate statistics and persist results into the database."
    )
    parser_analyze.add_argument(
        "--tool", 
        type=str, 
        default=None, 
        help="Name of the tool to analyze (e.g., ASICS). If omitted, analyzes all."
    )

    # Command: plot
    subparsers.add_parser(
        "plot", 
        help="Generate and save final statistical plots."
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route the command
    try:
        if args.command == "standardize":
            run_standardize()
        elif args.command == "ingest":
            run_ingestion(args.dir)
        elif args.command == "analyze":
            run_analysis(args.tool)
        elif args.command == "plot":
            run_plots()
    except Exception as e:
        logger.error("An error occurred during execution: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()