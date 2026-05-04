import pytest
import pandas as pd
from src.readers.csv_reader import CSVReader

def test_csv_reader(tmp_path): #deve_ler_arquivo_corretamente 
    # 1. PREPARAÇÃO: Criamos um arquivo CSV temporário real
    d = tmp_path / "sub"
    d.mkdir()
    file_path = d / "test.csv"
    
    df_original = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    df_original.to_csv(file_path, index=False)
    
    # 2. AÇÃO: Usamos o nosso Reader para ler esse arquivo
    reader = CSVReader()
    resultado = reader.read(str(file_path))
    
    # 3. VERIFICAÇÃO: O dado lido é igual ao que escrevemos?
    pd.testing.assert_frame_equal(resultado, df_original)

def test_csv_reader(): #deve_lancar_erro_se_arquivo_nao_existir 
    reader = CSVReader()
    with pytest.raises(RuntimeError) as excinfo:
        reader.read("caminho/que/nao/existe.csv")
    
    assert "Error reading CSV file" in str(excinfo.value)
