import pytest
import pandas as pd
from src.cleaners.nmRanalysis_cleaner import NmRanalysisCleaner

def test_nmranalysis_cleaner():
# preparação -> Cria mock com problema proposital 
    fake_mock = pd.DataFrame({
        "Sample":["Amostra_1", "Amostra_1"],  
        "Metabolite":["Alanine", "Alanine"], #duplicado
        "Fitting Error":[0.05, 0.01],
        "Quantity":[1.5, 1.8]
    })

    cleaner = NmRanalysisCleaner()
    
    # testar dados com um script
    resultado = cleaner.clean(fake_mock)

    # Verificação assertiva
    assert len(resultado) == 1
    
    # Espera-se que a quantidade seja a do menor erro
    assert resultado.iloc[0]["Quantity"] == 1.8