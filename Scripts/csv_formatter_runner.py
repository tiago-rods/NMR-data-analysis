import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.readers.csv_reader import CSVReader
from src.processors.data_processor import DataProcessor

from src.cleaners.ASICS_cleaner import ASICSCleaner
from src.cleaners.MagMet_cleaner import MagMetCleaner
from src.cleaners.nmRanalysis_cleaner import NmRanalysisCleaner

from src.formatter.ASICS_formatter import ASICSFormatter
from src.formatter.MagMet_formatter import MagMetFormatter
from src.formatter.nmRanalysis_formatter import NmRanalysisFormatter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def find_magmet_header_index(file_path: Path) -> int:
    with open(file_path, "r") as f:
        for idx, line in enumerate(f):
            if line.startswith("HMDB ID"):
                return idx
    return 0


def process_all_files(
    asics_dir: Path,
    magmet_dir: Path,
    nmranalysis_dir: Path,
    output_base_dir: Path,
) -> list[Optional[str]]:
    """Orchestrates the processing of all NMR tool CSV files.

    Args:
        asics_dir: Folder containing ASICS-generated CSVs.
        magmet_dir: Folder containing MagMet-generated CSVs.
        nmranalysis_dir: Folder containing nmRanalysis-generated CSVs.
        output_base_dir: Destination folder for standardized CSVs.

    Returns:
        List of paths to the generated files (None for failures).
    """
    reader = CSVReader()

    # Initialize processors
    asics_processor = DataProcessor(
        reader=reader,
        output_dir=str(output_base_dir),
        cleaner=ASICSCleaner(),
        formatter=ASICSFormatter(),
    )
    
    magmet_processor = DataProcessor(
        reader=reader,
        output_dir=str(output_base_dir),
        cleaner=MagMetCleaner(),
        formatter=MagMetFormatter(),
    )
    
    nmranalysis_processor = DataProcessor(
        reader=reader,
        output_dir=str(output_base_dir),
        cleaner=NmRanalysisCleaner(),
        formatter=NmRanalysisFormatter(),
    )

    asics_files: list[Path] = list(asics_dir.glob("*.csv"))
    magmet_files: list[Path] = list(magmet_dir.glob("*.csv"))
    nmranalysis_files: list[Path] = list(nmranalysis_dir.glob("*.csv"))

    logger.info(
        f"Found: {len(asics_files)} ASICS | "
        f"{len(magmet_files)} MagMet | "
        f"{len(nmranalysis_files)} nmRanalysis"
    )

    results: list[Optional[str]] = []

    # Process ASICS
    for file in asics_files:
        # ASICS index_col=0 handled via kwargs
        results.append(asics_processor.process(str(file), index_col=0))

    # Process MagMet
    for file in magmet_files:
        # Locate header for MagMet
        header_idx = find_magmet_header_index(file)
        results.append(magmet_processor.process(str(file), skiprows=header_idx))

    # Process nmRanalysis
    for file in nmranalysis_files:
        results.append(nmranalysis_processor.process(str(file), thousands=","))

    return results


if __name__ == "__main__":
    project_root: Path = Path(__file__).resolve().parent.parent

    process_all_files(
        asics_dir=project_root / "data" / "processed" / "ASICS",
        magmet_dir=project_root / "data" / "processed" / "MagMet",
        nmranalysis_dir=project_root / "data" / "raw" / "nmRanalysis",
        output_base_dir=project_root / "data" / "processed" / "formatted",
    )