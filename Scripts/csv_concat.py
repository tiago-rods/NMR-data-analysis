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
    'formatted_LNBio14_nmRanalysis_Urina_size45_unedited.csv',
    'formatted_LNBio15_nmRanalysis_Urina_size45_unedited.csv',
    'formatted_LNBio16_nmRanalysis_Urina_size45_unedited.csv',
    'formatted_LNBio17_nmRanalysis_Urina_size45_unedited.csv',
]

def sort_key(col_name: str) -> Union[int, str]:
    """
    Extrai o número inicial de nomes de colunas como '10_1H' para ordenação numérica.
    """
    if col_name == 'metabolite':
        return -1
    
    # Busca por dígitos no início da string usando regex
    if match := re.search(r'^(\d+)', col_name):
        return int(match.group(1))
    return col_name

def load_quant_data(file_name: str) -> Union[pd.DataFrame, None]:
    """Carrega um arquivo CSV individual e define o índice."""
    file_path = INPUT_DIR / file_name
    if not file_path.exists():
        print(f"  - [AVISO] Arquivo não encontrado: {file_name}")
        return None
    
    print(f"  - Carregando {file_name}...")
    return pd.read_csv(file_path).set_index('metabolite')

def concat_quantification_files():
    """Concatena, limpa e ordena arquivos de quantificação NMR."""
    print("Iniciando concatenação de arquivos...")

    # Pythonic: Uso de List Comprehension filtrando Nones
    dfs = [df for f in QUANT_FILES if (df := load_quant_data(f)) is not None]

    if not dfs:
        print("Erro: Nenhum dado carregado. Verifique os caminhos.")
        return

    # Concatenação e Limpeza
    # axis=1 (colunas), join='outer' (mantém todos os metabólitos)
    combined_df = pd.concat(dfs, axis=1, join='outer').fillna(0)

    # Ordenação Pythonic usando reindex com colunas ordenadas
    sorted_cols = sorted(combined_df.columns, key=sort_key)
    combined_df = combined_df.reindex(columns=sorted_cols)

    # Salvamento
    combined_df.to_csv(OUTPUT_FILE)

    print(f"\nSucesso! Arquivo consolidado: {OUTPUT_FILE.name}")
    print(f"Metabólitos: {len(combined_df)} | Experimentos: {len(combined_df.columns)}")

if __name__ == "__main__":
    concat_quantification_files()
