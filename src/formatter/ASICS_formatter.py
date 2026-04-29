import pandas as pd
import os
from typing import Optional
from src.formatter.factory_csv_formatter import FactoryCSVFormatter

class ASICSFormatter(FactoryCSVFormatter):
    def format(self, file_path: str) -> Optional[str]:
        """
        Formats ASICS CSV files.
        ASICS format: Rows are metabolites, columns are experiments.
        """
        try:
            # Read CSV
            df: pd.DataFrame = self.reader.read(file_path, index_col=0)
            
            # Clean experiment names (columns)
            df.columns = [str(col).replace('"', '').strip() for col in df.columns]
            
            # Clean metabolite names (index)
            df.index = [str(idx).replace('"', '').strip() for idx in df.index]
            df.index.name = 'metabolite'
            
            # Save to common format
            filename: str = os.path.basename(file_path)
            output_path: str = os.path.join(self.output_dir, f"formatted_{filename}")
            df.to_csv(output_path)
            print(f"Formatted ASICS file saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error processing ASICS file {file_path}: {e}")
            return None
