import logging
import os
import shutil
from pathlib import Path

from src.processors.data_processor import DataProcessor
from src.readers.xlsx_reader import XLSXReader
from src.cleaners.gold_standard_cleaner import GoldStandardCleaner
from src.formatter.gold_standard_formatter import GoldStandardFormatter

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1. Define paths
    raw_dir = Path("data/raw/Gold_Standard")
    output_dir = Path("data/processed/formatted/Complete")
    
    files_to_process = [
        {"path": raw_dir / "Urina/concentrations.xlsx", "out": "LNBioGS_Urina.csv"},
        {"path": raw_dir / "Soro/concentrations.xlsx", "out": "LNBioGS_Soro.csv"}
    ]

    # 2. Initialize Pipeline Components
    reader = XLSXReader()
    cleaner = GoldStandardCleaner()
    formatter = GoldStandardFormatter()
    
    processor = DataProcessor(
        reader=reader,
        cleaner=cleaner,
        formatter=formatter,
        output_dir=str(output_dir)
    )

    # 3. Execute
    for file_info in files_to_process:
        input_path = file_info["path"]
        target_name = file_info["out"]
        
        if not input_path.exists():
            logger.warning(f"File not found: {input_path}")
            continue

        # The DataProcessor saves as formatted_{filename}
        # We'll rename it to the target name
        temp_out = processor.process(str(input_path))
        
        if temp_out:
            final_path = output_dir / target_name
            # Move/Rename
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_out, final_path)
            logger.info(f"Gold Standard standardized successfully: {final_path}")

if __name__ == "__main__":
    main()
