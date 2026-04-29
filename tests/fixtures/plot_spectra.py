import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Add project root to PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.readers.csv_reader import CSVReader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def plot_nmr_spectra(csv_path: Path) -> None:
    """Reads a consolidated NMR CSV and plots its spectra.

    Follows the NMR convention: maximum PPM on the left, minimum on the right.

    Args:
        csv_path: Path to the consolidated NMR CSV file.
    """
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        return

    logger.info(f"Reading data from: {csv_path}")
    try:
        reader: CSVReader = CSVReader()
        df: pd.DataFrame = reader.read(str(csv_path))
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return

    if "PPM" not in df.columns:
        logger.error("Column 'PPM' not found in the CSV.")
        return

    ppm: pd.Series = df["PPM"]
    experiments: list[str] = [col for col in df.columns if col != "PPM"]

    if not experiments:
        logger.warning("No experiment columns found in the CSV.")
        return

    plt.figure(figsize=(12, 6))
    for exp in experiments:
        plt.plot(ppm, df[exp], label=exp, linewidth=1)

    plt.xlabel("Chemical Shift (PPM)")
    plt.ylabel("Intensity")
    plt.title("NMR Spectra Visualization")
    # plt.legend(loc='upper right', fontsize='small', ncol=2)

    # NMR convention: maximum PPM on the left
    plt.xlim(ppm.max(), ppm.min())
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    output_image: Path = csv_path.parent / f"spectra_plot_{csv_path.stem}.png"
    plt.savefig(output_image, dpi=300)
    logger.info(f"Plot saved to: {output_image}")
    # plt.show()


if __name__ == "__main__":
    base_dir: Path = Path(__file__).resolve().parent.parent.parent / "outputs" / "csv_tables"

    files_to_plot: list[str] = [
        "LNBio03_Bruker_600MHz_Urina_size180.csv",
        "LNBio04_Agilent_500MHz_Soro_size137.csv",
    ]

    for fname in files_to_plot:
        plot_nmr_spectra(base_dir / fname)
