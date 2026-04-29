import pandas as pd
import os
from typing import Optional
from src.formatter.factory_csv_formatter import FactoryCSVFormatter

class MagMetFormatter(FactoryCSVFormatter):
    def format(self, file_path: str) -> Optional[str]:
        """
        Formats MagMet CSV files.
        Skips metadata, removes HMDB ID, strips .fid from experiment names.
        """
        try:
            # MagMet files have metadata rows starting with #
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            header_idx: int = 0
            for i, line in enumerate(lines):
                if line.startswith('HMDB ID'):
                    header_idx = i
                    break
            
            # Read CSV starting from header row
            df: pd.DataFrame = self.reader.read(file_path, skiprows=header_idx)
            
            # Drop HMDB ID column if it exists
            if 'HMDB ID' in df.columns:
                df = df.drop(columns=['HMDB ID'])
            
            # Use 'Compound Name' as index and rename to 'metabolite'
            if 'Compound Name' in df.columns:
                df = df.set_index('Compound Name')
                df.index.name = 'metabolite'
            
            # Strip .fid from experiment names (columns)
            df.columns = [str(col).replace('.fid', '').strip() for col in df.columns]
            
            # Replace empty strings or missing values with 0
            df = df.fillna(0)
            df = df.replace('', 0)
            
            # Ensure numeric values
            df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
 
            # Save to common format
            filename: str = os.path.basename(file_path)
            output_path: str = os.path.join(self.output_dir, f"formatted_{filename}")
            df.to_csv(output_path)
            print(f"Formatted MagMet file saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error processing MagMet file {file_path}: {e}")
            return None
