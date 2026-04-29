import pandas as pd
import os
import re
from typing import Optional
from src.formatter.factory_csv_formatter import FactoryCSVFormatter

class NmRanalysisFormatter(FactoryCSVFormatter):
    def format(self, file_path: str) -> Optional[str]:
        """
        Formats nmRanalysis CSV files.
        Selects the quantification instance with the lowest Fitting Error per Sample and Metabolite.
        Rows are metabolites, columns are samples.
        """
        try:
            # Read CSV, handling comma thousands separator
            df = pd.read_csv(file_path, thousands=',')
            
            # Ensure necessary columns are present
            required_cols = ['Sample', 'Metabolite', 'Quantity', 'Fitting Error']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
                    
            # Clean Metabolite names (extract base name)
            # Removes " [number]" at the end of the string
            df['Base_Metabolite'] = df['Metabolite'].str.replace(r'\s+\[\d+\]$', '', regex=True)
            
            # Coerce Fitting Error and Quantity to numeric to be safe
            df['Fitting Error'] = pd.to_numeric(df['Fitting Error'], errors='coerce')
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            
            # Find the row index with the minimum Fitting Error for each Sample and Base_Metabolite
            idx = df.groupby(['Sample', 'Base_Metabolite'])['Fitting Error'].idxmin()
            best_fits = df.loc[idx]
            
            # Clean Sample names (remove 'X' prefix if added by nmRanalysis)
            best_fits['Sample'] = best_fits['Sample'].astype(str).str.replace(r'^X', '', regex=True)
            
            # Pivot table: Rows = metabolite, Columns = Sample, Values = Quantity
            pivot_df = best_fits.pivot(index='Base_Metabolite', columns='Sample', values='Quantity')
            
            # Fill missing values with 0.0
            pivot_df = pivot_df.fillna(0.0)
            
            # Set index name
            pivot_df.index.name = 'metabolite'
            
            # Save to common format
            filename = os.path.basename(file_path)
            output_path = os.path.join(self.output_dir, f"formatted_{filename}")
            pivot_df.to_csv(output_path)
            print(f"Formatted nmRanalysis file saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error processing nmRanalysis file {file_path}: {e}")
            return None