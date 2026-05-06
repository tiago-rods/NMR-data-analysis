import logging
import sys
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# Add project root to PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.loaders.csv_loader import CSVLoader
from src.loaders.jdx_loader import JDXLoader
from src.processors.jdx_processor import JDXProcessor

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Sample types and their TSP reference peak search windows (ppm)
SAMPLE_TYPE_WINDOWS: dict[str, tuple[float, float]] = {
    "Soro": (-5.0, -2.0),
    "Urina": (-4.0, -1.0),
}


def _detect_sample_type(folder: Path, output_file: Path) -> Optional[str]:
    """Detects the sample type automatically from the folder path or output filename.

    Args:
        folder: Path to the folder containing JDX files.
        output_file: Path to the output CSV file.

    Returns:
        The sample type name ('Soro' or 'Urina'), or None if not detected.
    """
    # Combine both paths into a single lower-case string for searching
    full_context = (str(folder) + str(output_file)).lower()

    if "urina" in full_context:
        return "Urina"
    if "soro" in full_context:
        return "Soro"
    
    return None


def main() -> None:
    # Data folder paths
    base_dir: Path = _ROOT
    jdx_folder: Path = base_dir / "data" / "raw" / "jdx" / "Urina" / "Subdivisao"  # -> change acquisition folder here
    output_folder: Path = base_dir / "outputs" / "csv_tables"                       # -> change output folder here
    output_file: Path = output_folder / "LNBio14_Bruker_600MHz_Urina_size45.csv"   # -> change output filename here

    if not jdx_folder.exists():
        logger.error(f"Folder not found: {jdx_folder}")
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    # Collect all JDX files
    jdx_files: list[Path] = list(jdx_folder.glob("*.jdx"))

    if not jdx_files:
        logger.warning(f"No JDX files found in: {jdx_folder}")
        return

    logger.info(f"Found {len(jdx_files)} files. Starting loading...")

    loader: JDXLoader = JDXLoader()
    formatter: JDXProcessor = JDXProcessor()
    csv_saver: CSVLoader = CSVLoader()

    jdx_data_list: list[dict[str, Any]] = []
    experiment_names: list[str] = []

    # Load files individually (EAFP: try and catch exceptions)
    for jdx_file in jdx_files:
        try:
            logger.info(f"Loading: {jdx_file.name}")
            data: dict[str, Any] = loader.load(str(jdx_file))
            jdx_data_list.append(data)
            experiment_names.append(jdx_file.stem)  # .stem strips the extension
        except Exception as e:
            logger.error(f"Failed to load {jdx_file.name}: {e}")

    if not jdx_data_list:
        logger.warning("No data loaded successfully.")
        return

    # Auto-detect sample type for TSP calibration
    sample_type: Optional[str] = _detect_sample_type(jdx_folder, output_file)
    if sample_type:
        logger.info(f"Sample type detected: '{sample_type}'. Applying automatic TSP calibration...")

    # Process and calibrate spectra
    try:
        final_df: pd.DataFrame = formatter.process(jdx_data_list, experiment_names, sample_type=sample_type)
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        return

    # Save consolidated CSV
    try:
        csv_saver.save(final_df, str(output_file))
        logger.info(f"CSV file successfully generated at: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")


if __name__ == "__main__":
    main()
