import pytest
import pandas as pd
import numpy as np
from src.cleaners.MagMet_cleaner import MagMetCleaner

def test_magmet_cleaner_deve_limpar_sufixos_e_tratar_erros():
    # 1. PREPARAÇÃO: Criando dados com sufixos .fid, colunas extras e valores não numéricos
    df_magmet = pd.DataFrame({
        "Compound Name": ["Valine", "Leucine"],
        "Amostra1.fid": ["1.5", "erro_de_leitura"], 
        "HMDB ID": ["HMDB001", "HMDB002"]
    })
    
    cleaner = MagMetCleaner()
    resultado = cleaner.clean(df_magmet)
    
    # 2. VERIFICAÇÃO:
    # Verificando se o sufixo .fid foi removido
    assert "Amostra1" in resultado.columns
    
    # Verificando se a coluna HMDB ID foi removida
    assert "HMDB ID" not in resultado.columns
    
    # Verificando se o índice foi definido corretamente
    assert resultado.index.name == "metabolite"
    assert "Valine" in resultado.index
    
    # Verificando a conversão numérica e tratamento de erros (deve virar 0.0)
    assert resultado.loc["Leucine", "Amostra1"] == 0.0
    assert isinstance(resultado.loc["Valine", "Amostra1"], (float, np.float64))
