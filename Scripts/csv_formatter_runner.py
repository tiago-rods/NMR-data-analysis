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

def process_all_files(asics_dir: str, magmet_dir: str, output_base_dir: str):
    """Orchestrates the processing of all files using the new class structure in src/formatter."""
    asics_formatter = ASICSFormatter(output_base_dir)
    magmet_formatter = MagMetFormatter(output_base_dir)

    asics_files = glob.glob(os.path.join(asics_dir, "*.csv"))
    magmet_files = glob.glob(os.path.join(magmet_dir, "*.csv"))
    
    print(f"Found {len(asics_files)} ASICS files and {len(magmet_files)} MagMet files.")
    
    results = []
    for f in asics_files:
        results.append(asics_formatter.format(f))
        
    for f in magmet_files:
        results.append(magmet_formatter.format(f))
        
    return results

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    asics_path = os.path.join(project_root, "data/processed/ASICS")
    magmet_path = os.path.join(project_root, "data/processed/MagMet")
    output_path = os.path.join(project_root, "data/processed/formatted")
    
    process_all_files(asics_path, magmet_path, output_path)
