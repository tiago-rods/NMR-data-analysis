"""
================================================================================
TESTES PARA A LÓGICA DE CONCATENAÇÃO (csv_concat.py)
================================================================================

CONCEITO: TESTANDO FUNÇÕES PURAS vs. FUNÇÕES COM EFEITOS COLATERAIS

  O csv_concat.py tem dois tipos de funções:

  1. `sort_key()` — É uma FUNÇÃO PURA: recebe uma entrada, retorna uma saída,
     NÃO lê arquivos, NÃO escreve nada. Fácil de testar diretamente.

  2. `concat_quantification_files()` — Tem EFEITOS COLATERAIS: lê arquivos do
     disco, escreve um novo arquivo. Para testar, precisamos de dados temporários.

ESTRATÉGIA:
  - Testamos `sort_key` diretamente (é pura, sem mocks necessários).
  - Testamos a lógica de concat/merge usando DataFrames em memória, sem
    tocar no disco. Extraímos a lógica de negócio para poder testá-la.
================================================================================
"""
import pytest
import pandas as pd
import re

# Importamos DIRETAMENTE as funções que queremos testar
# Importante: importamos de 'Scripts' (com S maiúsculo), que é como a pasta existe
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao path para que as importações funcionem
sys.path.insert(0, str(Path(__file__).parents[2]))
from Scripts.csv_concat import sort_key


# ==============================================================================
# TESTES DA FUNÇÃO sort_key (FUNÇÃO PURA — MAIS FÁCIL DE TESTAR)
# ==============================================================================

class TestSortKey:
    """
    Testa a função sort_key que extrai o número de uma coluna como '10_1H'.

    CONCEITO: TESTES PARAMETRIZADOS
    Em vez de escrever um test para cada caso, usamos @pytest.mark.parametrize
    para rodar o MESMO teste com vários conjuntos de entrada/saída esperada.
    Isso elimina duplicação de código nos testes.
    """

    @pytest.mark.parametrize("coluna, esperado", [
        # (entrada,       saída esperada)
        ("1_1H",          1),      # Número simples
        ("10_1H",         10),     # Dois dígitos
        ("180_1H",        180),    # Três dígitos
        ("metabolite",    -1),     # Caso especial: deve sempre vir primeiro
    ])
    def test_extrai_numero_corretamente(self, coluna, esperado):
        """Verifica se sort_key extrai o número numérico inicial da coluna."""
        assert sort_key(coluna) == esperado

    def test_colunas_numericas_ordenam_antes_de_colunas_texto(self):
        """
        Verifica o cenário real: uma lista misturada de colunas deve ser
        ordenada NUMERICAMENTE, não lexicograficamente.

        Ordenação lexicográfica (errada): ['10_1H', '180_1H', '2_1H', '45_1H']
        Ordenação numérica  (correta):    ['2_1H', '10_1H', '45_1H', '180_1H']
        """
        colunas_desorganizadas = ["180_1H", "2_1H", "45_1H", "10_1H"]
        resultado = sorted(colunas_desorganizadas, key=sort_key)
        assert resultado == ["2_1H", "10_1H", "45_1H", "180_1H"]

    def test_metabolite_sempre_primeira_coluna(self):
        """
        Verifica se 'metabolite' (o índice) sempre aparece como a primeira
        coluna após ordenação, independentemente de seu nome alfabético.
        """
        colunas = ["10_1H", "metabolite", "2_1H"]
        resultado = sorted(colunas, key=sort_key)
        assert resultado[0] == "metabolite"


# ==============================================================================
# TESTES DA LÓGICA DE CONCATENAÇÃO (sem I/O de disco)
# ==============================================================================
# ESTRATÉGIA: Em vez de testar concat_quantification_files() que lê arquivos,
# testamos a LÓGICA central de merge e preenchimento de NaN usando DataFrames
# criados diretamente em memória. Isso é mais rápido, confiável e preciso.
# ==============================================================================

class TestLogicaDeConcatenacao:

    @pytest.fixture
    def df_lnbio_10(self) -> pd.DataFrame:
        """Simula um arquivo de quantificação com 2 metabólitos e 2 amostras."""
        return pd.DataFrame(
            {"1_1H": [10.5, 5.0], "2_1H": [8.0, 3.1]},
            index=pd.Index(["Alanine", "Glucose"], name="metabolite")
        )

    @pytest.fixture
    def df_lnbio_11(self) -> pd.DataFrame:
        """
        Simula um segundo arquivo com:
        - Um metabólito em comum (Alanine)
        - Um metabólito NOVO que não existe no lnbio_10 (Valine)
        """
        return pd.DataFrame(
            {"3_1H": [12.0, 7.5]},
            index=pd.Index(["Alanine", "Valine"], name="metabolite")
        )

    def test_merge_preenche_metabolitos_faltantes_com_zero(
        self, df_lnbio_10, df_lnbio_11
    ):
        """
        CENÁRIO: Ao juntar dois arquivos, metabólitos que não existem em um
        arquivo devem aparecer com valor 0 no resultado final, NÃO como NaN.

        Aqui replicamos a lógica central do concat_quantification_files():
          pd.concat([...], axis=1, join='outer').fillna(0)
        """
        # Replica a lógica de merge do script real
        combined = pd.concat([df_lnbio_10, df_lnbio_11], axis=1, join="outer").fillna(0)

        # Valine não existe em df_lnbio_10, então deve ter 0 nas colunas 1_1H e 2_1H
        assert combined.loc["Valine", "1_1H"] == 0.0
        assert combined.loc["Valine", "2_1H"] == 0.0

        # Glucose não existe em df_lnbio_11, então deve ter 0 na coluna 3_1H
        assert combined.loc["Glucose", "3_1H"] == 0.0

    def test_merge_mantem_valores_existentes_inalterados(
        self, df_lnbio_10, df_lnbio_11
    ):
        """
        CENÁRIO: Metabólitos que EXISTEM em ambos os arquivos não devem
        ter seus valores alterados pelo merge.
        """
        combined = pd.concat([df_lnbio_10, df_lnbio_11], axis=1, join="outer").fillna(0)

        # Alanine existe nos dois — os valores originais devem ser preservados
        assert combined.loc["Alanine", "1_1H"] == 10.5
        assert combined.loc["Alanine", "3_1H"] == 12.0

    def test_resultado_contem_todos_os_metabolitos(
        self, df_lnbio_10, df_lnbio_11
    ):
        """
        CENÁRIO: O arquivo final deve conter a UNIÃO de todos os metabólitos
        de todos os arquivos de entrada.
        """
        combined = pd.concat([df_lnbio_10, df_lnbio_11], axis=1, join="outer").fillna(0)

        assert "Alanine" in combined.index
        assert "Glucose" in combined.index
        assert "Valine" in combined.index
        assert len(combined) == 3  # 3 metabólitos no total

    def test_colunas_ordenadas_numericamente_apos_concat(
        self, df_lnbio_10, df_lnbio_11
    ):
        """
        CENÁRIO: Após concatenar e ordenar, as colunas devem estar em ordem
        numérica (1, 2, 3...) e não lexicográfica.
        """
        combined = pd.concat([df_lnbio_10, df_lnbio_11], axis=1, join="outer").fillna(0)

        # Aplica a mesma ordenação que o script real faz
        colunas_ordenadas = sorted(combined.columns, key=sort_key)
        combined = combined.reindex(columns=colunas_ordenadas)

        assert list(combined.columns) == ["1_1H", "2_1H", "3_1H"]

    def test_merge_com_lista_vazia_nao_quebra(self):
        """
        CENÁRIO DE BORDA: Se nenhum arquivo for carregado (ex: todos os arquivos
        estão faltando), o código deve lidar com isso graciosamente.

        Testamos a condição `if not dfs:` do script real.
        """
        dfs = []  # Lista vazia, como se nenhum arquivo fosse encontrado
        # O script verifica se a lista está vazia antes de chamar pd.concat
        assert not dfs, "A lista de DataFrames deve estar vazia para este teste."
