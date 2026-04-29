import os
import glob
import sys
from pathlib import Path

# Add project root to sys.path to allow absolute imports
root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from src.formatter.ASICS_formatter import ASICSFormatter
from src.formatter.MagMet_formatter import MagMetFormatter
from src.formatter.nmRanalysis_formatter import NmRanalysisFormatter

def process_all_files(asics_dir: str, magmet_dir: str, nmranalysis_dir: str, output_base_dir: str) -> list[Optional[str]]:
    """Orchestrates the processing of all files using the new class structure in src/formatter."""
    asics_formatter: ASICSFormatter = ASICSFormatter(output_base_dir)
    magmet_formatter: MagMetFormatter = MagMetFormatter(output_base_dir)
    nmranalysis_formatter: NmRanalysisFormatter = NmRanalysisFormatter(output_base_dir)

    asics_files: list[str] = glob.glob(os.path.join(asics_dir, "*.csv"))
    magmet_files: list[str] = glob.glob(os.path.join(magmet_dir, "*.csv"))
    nmranalysis_files: list[str] = glob.glob(os.path.join(nmranalysis_dir, "*.csv"))
    
    print(f"Found {len(asics_files)} ASICS files, {len(magmet_files)} MagMet files, and {len(nmranalysis_files)} nmRanalysis files.")
    
    results: list[Optional[str]] = []
    for f in asics_files:
        results.append(asics_formatter.format(f))
        
    for f in magmet_files:
        results.append(magmet_formatter.format(f))

    for f in nmranalysis_files:
        results.append(nmranalysis_formatter.format(f))
        
    return results

if __name__ == "__main__":
    project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    asics_path: str = os.path.join(project_root, "data/processed/ASICS")
    magmet_path: str = os.path.join(project_root, "data/processed/MagMet")
    nmranalysis_path: str = os.path.join(project_root, "data/raw/nmRanalysis")
    output_path: str = os.path.join(project_root, "data/processed/formatted")
    
    process_all_files(asics_path, magmet_path, nmranalysis_path, output_path)