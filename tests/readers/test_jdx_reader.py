import pytest
from unittest.mock import patch, MagicMock
from src.readers.jdx_reader import JDXReader

def test_jdx_reader_deve_chamar_nmrglue_corretamente():
    # 1. PREPARAÇÃO: Vamos "fingir" (mock) que o nmrglue existe e funciona
    # sem precisar carregar um arquivo de verdade
    mock_dic = {"TITLE": "Teste NMR"}
    mock_data = [0.1, 0.2, 0.3]
    
    # Fazemos o patch na função que o JDXReader chama
    with patch("nmrglue.jcampdx.read") as mock_ng_read:
        # Configuramos o que o "fingimento" deve retornar
        mock_ng_read.return_value = (mock_dic, mock_data)
        
        reader = JDXReader()
        resultado = reader.read("fake_path.jdx")
        
        # 2. VERIFICAÇÃO:
        # O Reader chamou a função do nmrglue com o caminho certo?
        mock_ng_read.assert_called_once_with("fake_path.jdx")
        
        # O resultado contém o que o nmrglue retornou?
        assert resultado["metadata"] == mock_dic
        assert resultado["data"] == mock_data

def test_jdx_reader_deve_lancar_erro_em_falha_de_leitura():
    with patch("nmrglue.jcampdx.read") as mock_ng_read:
        # Simulamos que o nmrglue deu erro
        mock_ng_read.side_effect = Exception("Falha técnica")
        
        reader = JDXReader()
        with pytest.raises(RuntimeError) as excinfo:
            reader.read("arquivo_corrompido.jdx")
            
        assert "Error reading JDX file" in str(excinfo.value)
