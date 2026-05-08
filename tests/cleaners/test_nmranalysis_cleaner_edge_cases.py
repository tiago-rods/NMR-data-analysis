"""
================================================================================
TESTES DE CASOS DE BORDA — NmRanalysisCleaner
================================================================================

CONCEITO: POR QUE TESTAR CASOS DE BORDA?

  O "caminho feliz" (happy path) — dados perfeitos entrando, dados limpos
  saindo — já está coberto em test_nmranalysis_cleaner.py.

  Casos de borda testam o que acontece quando os dados são IMPERFEITOS:
    - Colunas obrigatórias faltando
    - Prefixos "X" nos nomes de amostras
    - Múltiplos metabólitos duplicados com erros de fitting diferentes
    - Valores não numéricos em colunas numéricas

  Um sistema robusto deve falhar de forma PREVISÍVEL (levantando a exceção
  certa) ou se RECUPERAR corretamente desses casos.

CONCEITO: pytest.raises
  Quando esperamos que um código LEVANTE uma exceção, usamos:

    with pytest.raises(TipoDaExcecao):
        codigo_que_deve_falhar()

  Se a exceção não for levantada, o teste FALHA. Isso garante que o código
  faz a validação correta dos dados de entrada.
================================================================================
"""
import pytest
import pandas as pd
from src.cleaners.nmRanalysis_cleaner import NmRanalysisCleaner


@pytest.fixture
def cleaner() -> NmRanalysisCleaner:
    """Fixture que fornece uma instância limpa do cleaner para cada teste."""
    return NmRanalysisCleaner()


@pytest.fixture
def df_valido() -> pd.DataFrame:
    """DataFrame base com todas as colunas obrigatórias presentes."""
    return pd.DataFrame({
        "Sample":        ["X10", "X10", "X11"],
        "Metabolite":    ["Alanine [1]", "Alanine [2]", "Glucose"],
        "Quantity":      [1.5, 1.8, 3.0],
        "Fitting Error": [0.05, 0.01, 0.02],
    })


# ==============================================================================
# TESTES DE VALIDAÇÃO DE ENTRADA
# ==============================================================================

class TestNmRanalysisCleanerValidacao:

    def test_levanta_erro_se_coluna_sample_faltando(self, cleaner):
        """
        CENÁRIO DE BORDA: Arquivo sem a coluna 'Sample'.
        O cleaner deve REJEITAR o dado imediatamente com ValueError.
        """
        df_sem_sample = pd.DataFrame({
            # "Sample" está faltando propositalmente
            "Metabolite":    ["Alanine"],
            "Quantity":      [1.5],
            "Fitting Error": [0.05],
        })
        with pytest.raises(ValueError, match="Missing required columns"):
            cleaner.clean(df_sem_sample)

    def test_levanta_erro_se_coluna_quantity_faltando(self, cleaner):
        """CENÁRIO DE BORDA: Arquivo sem a coluna 'Quantity'."""
        df_sem_quantity = pd.DataFrame({
            "Sample":        ["S1"],
            "Metabolite":    ["Alanine"],
            # "Quantity" está faltando
            "Fitting Error": [0.05],
        })
        with pytest.raises(ValueError, match="Missing required columns"):
            cleaner.clean(df_sem_quantity)

    def test_levanta_erro_se_multiplas_colunas_faltando(self, cleaner):
        """CENÁRIO DE BORDA: Múltiplas colunas obrigatórias ausentes."""
        df_quase_vazio = pd.DataFrame({"Sample": ["S1"]})
        with pytest.raises(ValueError):
            cleaner.clean(df_quase_vazio)


# ==============================================================================
# TESTES DA LÓGICA DE LIMPEZA
# ==============================================================================

class TestNmRanalysisCleanerLogica:

    def test_remove_prefixo_X_do_nome_da_amostra(self, cleaner, df_valido):
        """
        CENÁRIO: Amostras com prefixo 'X' (ex: 'X10') devem ter o X removido.
        O nmRanalysis adiciona esse prefixo por padrão, mas não faz sentido
        no nosso esquema de dados.
        """
        resultado = cleaner.clean(df_valido)

        # Após limpeza, nenhuma amostra deve começar com 'X'
        assert not resultado["Sample"].str.startswith("X").any()
        assert "10" in resultado["Sample"].values
        assert "11" in resultado["Sample"].values

    def test_seleciona_metabolito_com_menor_fitting_error(self, cleaner, df_valido):
        """
        CENÁRIO: Quando há duplicatas de um metabólito (ex: Alanine [1] e
        Alanine [2]), o cleaner deve manter APENAS a linha com o menor
        Fitting Error.

        No df_valido: Alanine [1] tem erro=0.05, Alanine [2] tem erro=0.01
        Resultado esperado: mantém Alanine [2] (erro menor), descarta Alanine [1]
        """
        resultado = cleaner.clean(df_valido)

        # Deve sobrar apenas 1 linha para Alanine na amostra X10 (agora "10")
        alanine_10 = resultado[resultado["Sample"] == "10"]
        assert len(alanine_10) == 1
        # E a quantidade deve ser a do menor erro (erro=0.01 -> Quantidade=1.8)
        assert alanine_10.iloc[0]["Quantity"] == 1.8

    def test_extrai_base_metabolite_corretamente(self, cleaner, df_valido):
        """
        CENÁRIO: 'Alanine [1]' e 'Alanine [2]' devem ser agrupados sob
        o mesmo Base_Metabolite = 'Alanine'.
        """
        resultado = cleaner.clean(df_valido)
        assert "Base_Metabolite" in resultado.columns
        assert "Alanine" in resultado["Base_Metabolite"].values

    def test_colunas_numericas_sao_convertidas(self, cleaner):
        """
        CENÁRIO DE BORDA: Colunas numéricas chegam como string (comum em CSVs).
        O cleaner deve convertê-las para float.
        """
        df_strings = pd.DataFrame({
            "Sample":        ["S1"],
            "Metabolite":    ["Alanine"],
            "Quantity":      ["1.5"],       # string, não float
            "Fitting Error": ["0.05"],      # string, não float
        })
        resultado = cleaner.clean(df_strings)
        assert resultado["Quantity"].dtype in ["float64", "float32"]
        assert resultado["Fitting Error"].dtype in ["float64", "float32"]

    def test_sem_duplicatas_apos_limpeza(self, cleaner, df_valido):
        """
        CENÁRIO: Após a limpeza, não deve haver combinações duplicadas de
        (Sample, Base_Metabolite).
        """
        resultado = cleaner.clean(df_valido)
        duplicatas = resultado.duplicated(subset=["Sample", "Base_Metabolite"]).sum()
        assert duplicatas == 0, f"Encontradas {duplicatas} duplicatas!"


# ==============================================================================
# TESTES DE CASOS EXTREMOS
# ==============================================================================

class TestNmRanalysisCleanerCasosExtremos:

    def test_dataframe_com_uma_unica_linha(self, cleaner):
        """CASO EXTREMO: Um arquivo com apenas 1 amostra e 1 metabólito."""
        df_minimo = pd.DataFrame({
            "Sample":        ["S1"],
            "Metabolite":    ["Alanine"],
            "Quantity":      [1.0],
            "Fitting Error": [0.1],
        })
        resultado = cleaner.clean(df_minimo)
        assert len(resultado) == 1

    def test_valores_nan_em_fitting_error_sao_tratados(self, cleaner):
        """
        CASO EXTREMO: NaN em Fitting Error.
        O cleaner usa idxmin() que ignora NaN por padrão, então a linha
        com valor válido deve ser selecionada.
        """
        df_com_nan = pd.DataFrame({
            "Sample":        ["S1", "S1"],
            "Metabolite":    ["Alanine [1]", "Alanine [2]"],
            "Quantity":      [1.5, 1.8],
            "Fitting Error": [float("nan"), 0.01],  # Primeiro é NaN
        })
        resultado = cleaner.clean(df_com_nan)
        # Deve selecionar a linha com erro 0.01 (o NaN é ignorado)
        assert len(resultado) == 1
        assert resultado.iloc[0]["Quantity"] == 1.8
