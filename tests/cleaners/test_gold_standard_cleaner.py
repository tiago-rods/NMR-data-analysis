"""
================================================================================
TESTES DO GoldStandardCleaner (src/cleaners/gold_standard_cleaner.py)
================================================================================

CONCEITO: O QUE ESTAMOS TESTANDO?

  O GoldStandardCleaner processa arquivos Excel exportados pelo Chenomx.
  Esses arquivos têm um cabeçalho multi-linha complexo:
    - Linha 0: Metadados (Data de exportação, etc)
    - Linha 1: Nomes dos Metabólitos
    - Linha 2 (Opcional): IDs HMDB (presente na Urina, ausente no Soro)
    - Linha 3+: Dados (Coluna 0 tem sufixo .cnx)

  O teste garante que o Cleaner identifica corretamente onde começam os dados
  e extrai os nomes dos metabólitos independente da presença da linha HMDB.

================================================================================
"""
import pytest
import pandas as pd
import numpy as np
from src.cleaners.gold_standard_cleaner import GoldStandardCleaner


@pytest.fixture
def cleaner() -> GoldStandardCleaner:
    return GoldStandardCleaner()


class TestGoldStandardCleaner:
    """Testes para a lógica de limpeza de arquivos Gold Standard (Chenomx)."""

    def test_limpa_formato_com_linha_hmdb_ex_urina(self, cleaner):
        """
        CENÁRIO: O arquivo tem uma linha com 'HMDB Accession Number' entre
        os nomes dos metabólitos e os dados. (Padrão Urina)
        """
        data = {
            "Col0": ["Export Date", "Sample", "HMDB Accession Number", "01RCF.cnx", "02RCF.cnx"],
            "Col1": [np.nan, "Alanine", "HMDB001", 10.5, 11.0],
            "Col2": [np.nan, "Glucose", "HMDB002", 200.0, 210.0]
        }
        df_raw = pd.DataFrame(data)
        
        resultado = cleaner.clean(df_raw)
        
        # 1. Deve identificar 'Sample' como a primeira coluna
        assert "Sample" in resultado.columns
        # 2. Deve usar os nomes dos metabólitos (Alanine, Glucose) como colunas
        assert "Alanine" in resultado.columns
        assert "Glucose" in resultado.columns
        # 3. Deve remover o sufixo .cnx dos nomes das amostras
        assert "01RCF" in resultado["Sample"].values
        # 4. Deve conter os valores numéricos corretos
        assert resultado.loc[resultado["Sample"] == "01RCF", "Alanine"].iloc[0] == 10.5

    def test_limpa_formato_sem_linha_hmdb_ex_soro(self, cleaner):
        """
        CENÁRIO: O arquivo NÃO tem a linha HMDB. Os dados começam logo após
        os nomes dos metabólitos. (Padrão Soro)
        """
        data = {
            "Col0": ["Export Date", "Sample", "1_1H.cnx", "2_1H.cnx"],
            "Col1": [np.nan, "Valine", 5.5, 6.0],
            "Col2": [np.nan, "Leucine", 8.2, 9.0]
        }
        df_raw = pd.DataFrame(data)
        
        resultado = cleaner.clean(df_raw)
        
        assert "Sample" in resultado.columns
        assert "Valine" in resultado.columns
        assert "1_1H" in resultado["Sample"].values
        assert resultado.loc[resultado["Sample"] == "1_1H", "Valine"].iloc[0] == 5.5

    def test_converte_valores_nao_numericos_para_zero(self, cleaner):
        """
        CENÁRIO DE BORDA: Se houver um erro de leitura (texto onde deveria ser número),
        o cleaner deve converter para 0.0 e não quebrar.
        """
        data = {
            "Col0": ["Sample", "Metabolite", "1_1H.cnx"],
            "Col1": ["NaN", "Alanine", "ERRO_LEITURA"]
        }
        df_raw = pd.DataFrame(data)
        
        resultado = cleaner.clean(df_raw)
        assert resultado["Alanine"].iloc[0] == 0.0

    def test_retorna_original_se_nao_encontrar_cnx(self, cleaner):
        """
        CENÁRIO DE ERRO: Se o arquivo não tiver nenhuma linha terminando em .cnx,
        o cleaner deve avisar e retornar o dado bruto em vez de quebrar.
        """
        df_errado = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        
        resultado = cleaner.clean(df_errado)
        # Deve retornar o mesmo DataFrame (ou logar o erro e retornar)
        assert len(resultado) == 2
        assert "A" in resultado.columns

    def test_remove_espacos_extras_no_nome_da_amostra(self, cleaner):
        """O cleaner deve fazer trim nos nomes das amostras."""
        data = {
            "Col0": ["Sample", "Metabolite", " 01RCF.cnx "], # Espaços aqui
            "Col1": ["NaN", "Alanine", 10.0]
        }
        df_raw = pd.DataFrame(data)
        
        resultado = cleaner.clean(df_raw)
        assert "01RCF" in resultado["Sample"].values
