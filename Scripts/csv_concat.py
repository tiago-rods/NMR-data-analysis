import pandas as pd
import re
from pathlib import Path
from typing import List, Union

# Configurações de Caminho
BASE_DIR = Path(r'c:\Iniciacao Cientifica\Data_Analysis\NMR-data-analysis')
INPUT_DIR = BASE_DIR / 'data' / 'processed' / 'formatted'
OUTPUT_FILE = INPUT_DIR / 'concatenated_quantification.csv'

# Lista específica de arquivos solicitada
QUANT_FILES = [
    'formatted_LNBio20_Agilent_500MHz_Soro_nmRanalysis_size46_unedited.csv',
    'formatted_LNBio21_Agilent_500MHz_Soro_nmRanalysis_size46_unedited.csv',
    'formatted_LNBio22_Agilent_500MHz_Soro_nmRanalysis_size46_unedited.csv',
]

def sort_key(col_name: str) -> Union[int, str]:
    """
    Extracts the initial number from column names like '10_1H' for numerical sorting.
    """
    if col_name == 'metabolite':
        return -1
    
    # Extracts the initial number from column names like '10_1H' using regex
    if match := re.search(r'^(\d+)', col_name):
        return int(match.group(1))
    return col_name

def load_quant_data(file_name: str) -> Union[pd.DataFrame, None]:
    """Loads a single CSV file and sets the index."""
    file_path = INPUT_DIR / file_name
    if not file_path.exists():
        print(f"  - [WARNING] File not found: {file_name}")
        return None
    
    print(f"  - Loading {file_name}...")
    return pd.read_csv(file_path).set_index('metabolite')

def concat_quantification_files():
    """Concatenates, cleans and orders NMR quantification files."""
    print("Starting file concatenation...")

    # Pythonic: Uso de List Comprehension filtrando Nones
    dfs = [df for f in QUANT_FILES if (df := load_quant_data(f)) is not None]

    if not dfs:
        print("Error: No data loaded. Please check the paths.")
        return

    # Concatenation and Cleaning
    # axis=1 (colunas), join='outer' (mantém todos os metabólitos)
    combined_df = pd.concat(dfs, axis=1, join='outer').fillna(0)

    # Pythonic ordering using reindex with sorted columns
    sorted_cols = sorted(combined_df.columns, key=sort_key)
    combined_df = combined_df.reindex(columns=sorted_cols)

    # Saving
    combined_df.to_csv(OUTPUT_FILE)

    print(f"\nSuccess! Consolidated file: {OUTPUT_FILE.name}")
    print(f"Metabolites: {len(combined_df)} | Experiments: {len(combined_df.columns)}")

if __name__ == "__main__":
    concat_quantification_files()
