import pytest
import pandas as pd
from src.cleaners.ASICS_cleaner import ASICSCleaner

def test_asics_cleaner_deve_remover_aspas_e_espacos():
    # 1. PREPARAÇÃO: Note as aspas e espaços nos nomes
    df_sujo = pd.DataFrame(
        {" \"Amostra_1\" ": [10.5], " Amostra_2 ": [20.0]}, 
        index=[" \"Alanine\" ", " Glucose "]
    )
    
    cleaner = ASICSCleaner()
    resultado = cleaner.clean(df_sujo)
    
    # 2. VERIFICAÇÃO: 
    # O nome da coluna deve estar limpo
    assert "Amostra_1" in resultado.columns
    assert "Amostra_2" in resultado.columns
    
    # O nome do metabólito (índice) deve estar limpo
    assert resultado.index[0] == "Alanine"
    assert resultado.index[1] == "Glucose"
    assert resultado.index.name == "metabolite"
