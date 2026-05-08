"""
================================================================================
TESTES DE CASOS DE BORDA — ASICSCleaner e MagMetCleaner
================================================================================

CONCEITO: POR QUE TESTAR CADA FERRAMENTA SEPARADAMENTE?

  Cada software de análise NMR (ASICS, MagMet, nmRanalysis) tem suas próprias
  "manias" de formato. Um CSV do ASICS pode ter aspas extras nos nomes.
  Um CSV do MagMet pode ter sufixos '.fid' ou colunas de metadados como 'HMDB ID'.

  Se você receber dados de um NOVO experimento com uma variação pequena no
  formato (ex: espaço a mais, aspas simples em vez de duplas), esses testes
  vão detectar que o Cleaner não está tratando o novo caso.

NOVIDADE — TESTES PARAMETRIZADOS COM MAIS COMPLEXIDADE:
  Vamos usar @pytest.mark.parametrize com IDs para tornar a saída do pytest
  mais legível. Em vez de mostrar "test[param0]", vai mostrar "test[aspa-dupla]".

================================================================================
"""
import pytest
import pandas as pd
import numpy as np

from src.cleaners.ASICS_cleaner import ASICSCleaner
from src.cleaners.MagMet_cleaner import MagMetCleaner


# ==============================================================================
# TESTES DE BORDA — ASICSCleaner
# ==============================================================================

class TestASICSCleanerEdgeCases:
    """
    O ASICSCleaner limpa nomes de colunas (amostras) e do índice (metabólitos).
    Ele deve remover aspas e espaços extras de QUALQUER combinação.
    """

    @pytest.mark.parametrize("coluna_suja, coluna_limpa", [
        # (entrada com sujeira,        saída esperada)
        (' "Amostra_1" ',             "Amostra_1"),   # aspas duplas + espaços
        (' Amostra_2 ',              "Amostra_2"),    # só espaços
        ('"Amostra_3"',              "Amostra_3"),    # aspas sem espaços
        ('Amostra_4',                "Amostra_4"),    # já limpo — deve permanecer
    ], ids=["aspas-e-espacos", "so-espacos", "so-aspas", "ja-limpo"])
    def test_limpa_nomes_de_colunas(self, coluna_suja, coluna_limpa):
        """
        CENÁRIO PARAMETRIZADO: Verifica que o Cleaner limpa vários tipos
        de sujeira nos nomes de colunas (amostras).

        Cada linha do parametrize é um teste separado com seu próprio ID.
        """
        df = pd.DataFrame(
            {coluna_suja: [1.0]},
            index=pd.Index(["Alanine"], name="metabolite")
        )
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df)
        assert coluna_limpa in resultado.columns

    @pytest.mark.parametrize("metabolito_sujo, metabolito_limpo", [
        (' "Alanine" ',  "Alanine"),
        (' Glucose ',    "Glucose"),
        ('"Valine"',     "Valine"),
    ], ids=["aspas-e-espacos", "so-espacos", "so-aspas"])
    def test_limpa_nomes_de_metabolitos_no_indice(self, metabolito_sujo, metabolito_limpo):
        """CENÁRIO PARAMETRIZADO: Mesma verificação, mas para o índice (metabolitos)."""
        df = pd.DataFrame(
            {"Amostra1": [1.0]},
            index=pd.Index([metabolito_sujo])
        )
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df)
        assert metabolito_limpo in resultado.index

    def test_indice_recebe_nome_metabolite(self):
        """
        CENÁRIO SIMPLES: O índice do DataFrame limpo deve sempre se chamar
        'metabolite', independentemente do nome original.
        """
        df = pd.DataFrame({"S1": [1.0]}, index=pd.Index(["Alanine"]))
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df)
        assert resultado.index.name == "metabolite"

    def test_valores_numericos_nao_sao_alterados(self):
        """
        CENÁRIO DE BORDA: A limpeza de nomes não deve tocar nos valores numéricos.
        """
        df = pd.DataFrame(
            {' "S1" ': [10.5, 99.9]},
            index=pd.Index(['"Alanine"', '"Glucose"'])
        )
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df)

        # Os valores devem ser os mesmos
        assert resultado.loc["Alanine", "S1"] == 10.5
        assert resultado.loc["Glucose", "S1"] == 99.9

    def test_dataframe_vazio_nao_quebra(self):
        """
        CASO EXTREMO: DataFrame sem linhas (colunas existem, mas não há dados).
        Não deve lançar exceção — simplesmente retorna vazio e limpo.
        """
        df = pd.DataFrame(columns=[' "S1" ', ' "S2" '])
        df.index.name = None
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df)

        assert "S1" in resultado.columns
        assert "S2" in resultado.columns
        assert resultado.index.name == "metabolite"


# ==============================================================================
# TESTES DE BORDA — MagMetCleaner
# ==============================================================================

class TestMagMetCleanerEdgeCases:
    """
    O MagMetCleaner remove sufixos '.fid', descarta 'HMDB ID', define o índice
    a partir de 'Compound Name' e converte tudo para numérico.
    """

    @pytest.fixture
    def df_magmet_padrao(self) -> pd.DataFrame:
        """DataFrame padrão com todos os "problemas" típicos do MagMet."""
        return pd.DataFrame({
            "Compound Name": ["Valine", "Leucine", "Alanine"],
            "HMDB ID":       ["HMDB001", "HMDB002", "HMDB003"],
            "Amostra1.fid":  [1.5, 2.0, 3.0],
            "Amostra2.fid":  [4.0, 5.0, 6.0],
        })

    def test_remove_sufixo_fid_de_todos_os_experimentos(self, df_magmet_padrao):
        """
        CENÁRIO: Todas as colunas de experimentos com '.fid' devem ter
        o sufixo removido.
        """
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df_magmet_padrao)

        assert "Amostra1" in resultado.columns
        assert "Amostra2" in resultado.columns
        assert not any(".fid" in str(col) for col in resultado.columns)

    def test_remove_coluna_hmdb_id(self, df_magmet_padrao):
        """CENÁRIO: A coluna 'HMDB ID' deve ser descartada."""
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df_magmet_padrao)
        assert "HMDB ID" not in resultado.columns

    def test_define_compound_name_como_indice(self, df_magmet_padrao):
        """CENÁRIO: 'Compound Name' vira o índice com nome 'metabolite'."""
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df_magmet_padrao)

        assert resultado.index.name == "metabolite"
        assert "Valine" in resultado.index
        assert "Compound Name" not in resultado.columns

    def test_valores_nao_numericos_viram_zero(self):
        """
        CENÁRIO DE BORDA: Células com texto (erros de leitura do instrumento)
        devem ser convertidas para 0.0, não deixadas como NaN ou string.
        """
        df = pd.DataFrame({
            "Compound Name": ["Valine"],
            "Amostra1.fid":  ["ERRO"],     # Texto inválido
            "Amostra2.fid":  ["N/A"],      # Outro texto inválido
        })
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df)

        assert resultado.loc["Valine", "Amostra1"] == 0.0
        assert resultado.loc["Valine", "Amostra2"] == 0.0

    def test_valores_nan_viram_zero(self):
        """
        CENÁRIO DE BORDA: Células com NaN (comuns em arquivos com dados
        faltantes) devem virar 0.0.
        """
        df = pd.DataFrame({
            "Compound Name": ["Valine", "Leucine"],
            "Amostra1.fid":  [1.5, float("nan")],  # NaN aqui
        })
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df)

        assert resultado.loc["Leucine", "Amostra1"] == 0.0

    def test_sem_coluna_hmdb_id_nao_quebra(self):
        """
        CENÁRIO DE BORDA: Arquivo MagMet que não tem coluna 'HMDB ID'.
        O Cleaner deve funcionar sem erros.
        """
        df = pd.DataFrame({
            "Compound Name": ["Valine"],
            "Amostra1.fid":  [1.5],
            # 'HMDB ID' intencionalmente ausente
        })
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df)  # Não deve levantar KeyError

        assert resultado.index.name == "metabolite"
        assert "Valine" in resultado.index

    def test_sem_sufixo_fid_nas_colunas_nao_quebra(self):
        """
        CENÁRIO DE BORDA: Arquivo MagMet que já não tem sufixo '.fid'
        nos nomes dos experimentos (ex: arquivo pré-processado).
        Deve funcionar normalmente.
        """
        df = pd.DataFrame({
            "Compound Name": ["Valine"],
            "Amostra1":      [1.5],    # Sem .fid
        })
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df)

        assert "Amostra1" in resultado.columns

    @pytest.mark.parametrize("valor, esperado", [
        (0,            0.0),   # Zero já é válido
        (1.5,          1.5),   # Float normal
        ("2.7",        2.7),   # String numérica válida
        ("erro",       0.0),   # String inválida -> 0
        (float("nan"), 0.0),   # NaN -> 0
    ], ids=["zero", "float", "string-valida", "string-invalida", "nan"])
    def test_conversao_numerica_parametrizada(self, valor, esperado):
        """
        CENÁRIO PARAMETRIZADO: Verifica a conversão numérica para todos os
        tipos de valores que podem aparecer em um arquivo MagMet real.
        """
        df = pd.DataFrame({
            "Compound Name": ["Valine"],
            "Amostra1.fid":  [valor],
        })
        cleaner = MagMetCleaner()
        resultado = cleaner.clean(df)

        assert resultado.loc["Valine", "Amostra1"] == pytest.approx(esperado)
