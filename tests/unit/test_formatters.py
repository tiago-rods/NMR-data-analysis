"""
================================================================================
TESTES DOS FORMATADORES (src/formatter/)
================================================================================

CONCEITO: O QUE FAZ UM FORMATADOR?

  Depois que o Cleaner limpa os dados (remove duplicatas, trata NaN, etc.),
  o Formatter reestrutura o DataFrame para o formato "padrão" do projeto:

      FORMATO PADRÃO:
        - Linhas (index) = metabólitos
        - Colunas        = amostras/experimentos

  O NmRanalysisFormatter precisa fazer um PIVOT (rotação) porque os dados
  brutos do nmRanalysis chegam em formato "longo" (cada linha é uma
  combinação Sample+Metabolite). Os formatadores ASICS e MagMet já chegam
  no formato correto após a limpeza, então apenas repassam o DataFrame.

CONCEITO: PIVOT TABLE
  Um pivot transforma formato "longo":
    Sample   | Metabolite | Quantity
    S1       | Alanine    | 1.5
    S1       | Glucose    | 2.0
    S2       | Alanine    | 3.0

  Em formato "largo" (o nosso padrão):
    metabolite | S1  | S2
    Alanine    | 1.5 | 3.0
    Glucose    | 2.0 | 0.0

================================================================================
"""
import pytest
import pandas as pd

from src.formatter.nmRanalysis_formatter import NmRanalysisFormatter
from src.formatter.ASICS_formatter import ASICSFormatter
from src.formatter.MagMet_formatter import MagMetFormatter


# ==============================================================================
# TESTES DO NmRanalysisFormatter (o mais complexo — faz pivot)
# ==============================================================================

class TestNmRanalysisFormatter:

    @pytest.fixture
    def df_limpo(self) -> pd.DataFrame:
        """
        Simula o DataFrame APÓS a limpeza pelo NmRanalysisCleaner.
        Já tem 'Base_Metabolite' (sem sufixos [1], [2]) e 'Sample' sem 'X'.
        Este é o formato "longo" que o formatter recebe.
        """
        return pd.DataFrame({
            "Sample":          ["10", "10", "11", "11"],
            "Base_Metabolite": ["Alanine", "Glucose", "Alanine", "Glucose"],
            "Quantity":        [1.5,       2.0,       3.0,       4.5],
            "Fitting Error":   [0.01,      0.02,      0.01,      0.03],
        })

    def test_formato_saida_tem_metabolitos_nas_linhas(self, df_limpo):
        """
        OBJETIVO: Verificar que após o pivot, as LINHAS representam metabólitos.
        O índice do DataFrame deve se chamar 'metabolite'.
        """
        formatter = NmRanalysisFormatter()
        resultado = formatter.format(df_limpo)

        assert resultado.index.name == "metabolite"
        assert "Alanine" in resultado.index
        assert "Glucose" in resultado.index

    def test_formato_saida_tem_amostras_nas_colunas(self, df_limpo):
        """
        OBJETIVO: Verificar que após o pivot, as COLUNAS representam amostras.
        """
        formatter = NmRanalysisFormatter()
        resultado = formatter.format(df_limpo)

        assert "10" in resultado.columns
        assert "11" in resultado.columns

    def test_valores_corretos_apos_pivot(self, df_limpo):
        """
        OBJETIVO: Verificar se os valores numéricos estão nas posições certas
        após a rotação da tabela.

        Alanine na amostra "10" deve valer 1.5
        Glucose na amostra "11" deve valer 4.5
        """
        formatter = NmRanalysisFormatter()
        resultado = formatter.format(df_limpo)

        assert resultado.loc["Alanine", "10"] == 1.5
        assert resultado.loc["Glucose", "10"] == 2.0
        assert resultado.loc["Alanine", "11"] == 3.0
        assert resultado.loc["Glucose", "11"] == 4.5

    def test_metabolito_ausente_em_amostra_vira_zero(self):
        """
        CENÁRIO DE BORDA: Se um metabólito existe em S1 mas NÃO em S2,
        o pivot deve preencher o valor faltante com 0.0 (não NaN).
        """
        df_incompleto = pd.DataFrame({
            "Sample":          ["S1", "S2"],
            "Base_Metabolite": ["Alanine", "Glucose"],  # Metabolitos diferentes
            "Quantity":        [1.5, 2.0],
            "Fitting Error":   [0.01, 0.02],
        })
        formatter = NmRanalysisFormatter()
        resultado = formatter.format(df_incompleto)

        # Alanine não foi medida em S2, então deve ser 0.0
        assert resultado.loc["Alanine", "S2"] == 0.0
        # Glucose não foi medida em S1, então deve ser 0.0
        assert resultado.loc["Glucose", "S1"] == 0.0

    def test_resultado_nao_tem_nan(self, df_limpo):
        """
        OBJETIVO: O DataFrame final não deve conter nenhum valor NaN.
        Todos os valores faltantes devem ter sido preenchidos com 0.0.
        """
        formatter = NmRanalysisFormatter()
        resultado = formatter.format(df_limpo)
        assert not resultado.isnull().any().any(), "DataFrame contém NaN!"


# ==============================================================================
# TESTES DO ASICSFormatter (passa o dado como está — simples, mas importante)
# ==============================================================================

class TestASICSFormatter:
    """
    O ASICSFormatter não precisa fazer pivot — o Cleaner já entrega no
    formato certo. Mas ainda precisamos testar que ele NÃO quebra os dados.
    """

    @pytest.fixture
    def df_asics_limpo(self) -> pd.DataFrame:
        """Simula saída do ASICSCleaner: index=metabolite, colunas=amostras."""
        return pd.DataFrame(
            {"S1": [10.5, 5.0], "S2": [8.0, 3.1]},
            index=pd.Index(["Alanine", "Glucose"], name="metabolite")
        )

    def test_formatter_preserva_estrutura_do_dado(self, df_asics_limpo):
        """
        O ASICS formatter não deve alterar nada — só repassar o DataFrame.
        Verificamos que os valores e a estrutura estão intactos.
        """
        formatter = ASICSFormatter()
        resultado = formatter.format(df_asics_limpo)

        assert resultado.index.name == "metabolite"
        assert resultado.loc["Alanine", "S1"] == 10.5
        assert list(resultado.columns) == ["S1", "S2"]

    def test_formatter_retorna_dataframe(self, df_asics_limpo):
        """O formatter deve retornar um DataFrame, não None."""
        formatter = ASICSFormatter()
        resultado = formatter.format(df_asics_limpo)
        assert isinstance(resultado, pd.DataFrame)


# ==============================================================================
# TESTES DO MagMetFormatter
# ==============================================================================

class TestMagMetFormatter:
    """O MagMetFormatter também passa o dado como está após a limpeza."""

    @pytest.fixture
    def df_magmet_limpo(self) -> pd.DataFrame:
        """Simula saída do MagMetCleaner: index=metabolite, colunas=amostras."""
        return pd.DataFrame(
            {"S1": [1.5, 2.0], "S2": [3.0, 0.0]},
            index=pd.Index(["Valine", "Leucine"], name="metabolite")
        )

    def test_formatter_preserva_estrutura_do_dado(self, df_magmet_limpo):
        """O MagMet formatter não deve alterar nada — verificamos integridade."""
        formatter = MagMetFormatter()
        resultado = formatter.format(df_magmet_limpo)

        assert resultado.index.name == "metabolite"
        assert resultado.loc["Valine", "S1"] == 1.5
        assert "Leucine" in resultado.index

    def test_formatter_retorna_dataframe(self, df_magmet_limpo):
        """O formatter deve retornar um DataFrame, não None."""
        formatter = MagMetFormatter()
        resultado = formatter.format(df_magmet_limpo)
        assert isinstance(resultado, pd.DataFrame)
