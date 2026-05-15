"""
================================================================================
TESTES DO csv_to_jsonb (src/ingestion/csv_to_jsonb.py)
================================================================================

CONCEITO: POR QUE TESTAR A CONVERSÃO PARA JSONB?

  A função convert_wide_to_jsonb é o elo entre os CSVs padronizados e as
  procedures PL/pgSQL do banco. Se ela gerar JSON com chaves erradas ou
  incluir valores zerados, a ingestão vai falhar silenciosamente.

  Esses testes garantem que o contrato com o banco é sempre respeitado:
    - Cada espectro vira uma chave no dicionário resultante.
    - Cada item do JSON tem exatamente as chaves 'metabolite' e 'concentration'.
    - Valores zero são filtrados (economia de banda e processamento).

================================================================================
"""
import json
import pytest
import pandas as pd

from src.ingestion.csv_to_jsonb import convert_wide_to_jsonb


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def df_padrao() -> pd.DataFrame:
    """DataFrame no formato padrão do projeto (metabolito=índice, amostras=colunas)."""
    return pd.DataFrame(
        {
            "S1": [100.0, 0.0, 50.5],
            "S2": [0.0, 200.0, 75.0],
        },
        index=pd.Index(["Alanine", "Glucose", "Valine"], name="metabolite")
    )


# ==============================================================================
# TESTES — Estrutura do JSON
# ==============================================================================

class TestCsvToJsonbEstrutura:
    """Testa a estrutura e o contrato de saída da função de conversão."""

    def test_retorna_um_dicionario(self, df_padrao):
        """A função deve retornar um dicionário Python."""
        resultado = convert_wide_to_jsonb(df_padrao)
        assert isinstance(resultado, dict)

    def test_chaves_sao_nomes_das_amostras(self, df_padrao):
        """As chaves do dicionário devem ser os nomes das colunas (amostras)."""
        resultado = convert_wide_to_jsonb(df_padrao)
        assert "S1" in resultado
        assert "S2" in resultado

    def test_valores_sao_strings_json_validas(self, df_padrao):
        """Os valores do dicionário devem ser strings JSON válidas e parseáveis."""
        resultado = convert_wide_to_jsonb(df_padrao)
        for espectro, json_str in resultado.items():
            parsed = json.loads(json_str)  # Não deve lançar exceção
            assert isinstance(parsed, list)

    def test_cada_item_tem_chave_metabolite(self, df_padrao):
        """Cada objeto dentro do JSON deve ter a chave 'metabolite'."""
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        for item in items_s1:
            assert "metabolite" in item

    def test_cada_item_tem_chave_concentration(self, df_padrao):
        """Cada objeto dentro do JSON deve ter a chave 'concentration'."""
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        for item in items_s1:
            assert "concentration" in item


# ==============================================================================
# TESTES — Filtragem de valores zerados
# ==============================================================================

class TestCsvToJsonbFiltragemZeros:
    """
    Testa que valores zerados são removidos do JSON final.
    Isso é importante para economizar banda e não enviar dados sem significado biológico.
    """

    def test_valores_zero_nao_aparecem_no_json(self, df_padrao):
        """
        CENÁRIO: Glucose em S1 tem valor 0.0. Ela NÃO deve aparecer no JSON de S1.
        """
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        metabolitos_s1 = [item["metabolite"] for item in items_s1]
        assert "Glucose" not in metabolitos_s1, "Glucose com valor 0 não deveria estar em S1"

    def test_valores_positivos_aparecem_no_json(self, df_padrao):
        """
        CENÁRIO: Alanine em S1 tem valor 100.0. Ela DEVE aparecer no JSON de S1.
        """
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        metabolitos_s1 = [item["metabolite"] for item in items_s1]
        assert "Alanine" in metabolitos_s1

    def test_amostra_com_todos_zeros_gera_lista_vazia(self):
        """
        CENÁRIO DE BORDA: Uma amostra onde todos os metabólitos foram zerados
        deve gerar um JSON com lista vazia — não deve quebrar.
        """
        df = pd.DataFrame(
            {"S_VAZIA": [0.0, 0.0]},
            index=pd.Index(["Alanine", "Glucose"], name="metabolite")
        )
        resultado = convert_wide_to_jsonb(df)
        items = json.loads(resultado["S_VAZIA"])
        assert items == []


# ==============================================================================
# TESTES — Valores numéricos corretos
# ==============================================================================

class TestCsvToJsonbValores:
    """Testa que os valores numéricos são preservados corretamente."""

    def test_valor_concentration_e_float(self, df_padrao):
        """O valor de 'concentration' deve ser float, não string."""
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        for item in items_s1:
            assert isinstance(item["concentration"], float)

    def test_valor_concentration_correto(self, df_padrao):
        """A concentração de Valine em S1 deve ser 50.5."""
        resultado = convert_wide_to_jsonb(df_padrao)
        items_s1 = json.loads(resultado["S1"])
        valine_item = next((i for i in items_s1 if i["metabolite"] == "Valine"), None)
        assert valine_item is not None
        assert valine_item["concentration"] == pytest.approx(50.5)

    def test_aceita_dataframe_com_coluna_metabolite_em_vez_de_indice(self):
        """
        CENÁRIO: Se 'metabolite' for coluna (não índice), a função deve normalizar
        e funcionar corretamente.
        """
        df = pd.DataFrame({
            "metabolite": ["Alanine", "Glucose"],
            "S1": [10.0, 20.0],
        })
        resultado = convert_wide_to_jsonb(df)
        assert "S1" in resultado
        items = json.loads(resultado["S1"])
        nomes = [i["metabolite"] for i in items]
        assert "Alanine" in nomes
        assert "Glucose" in nomes
