import pytest
import pandas as pd
from src.cleaners.ASICS_cleaner import ASICSCleaner


# ==============================================================================
# TESTES EXISTENTES — Formato Wide (padrão antigo)
# ==============================================================================

def test_asics_cleaner_deve_remover_aspas_e_espacos():
    # 1. PREPARAÇÃO: Note as aspas e espaços nos nomes
    df_sujo = pd.DataFrame(
        {" \"Amostra_1\" ": [10.5], " Amostra_2 ": [20.0]}, 
        index=[" \"Alanine\" ", " Glucose "]
    )
    
    cleaner = ASICSCleaner()
    resultado = cleaner.clean(df_sujo)
    
    # 2. VERIFICAÇÃO: 
    # O nome da coluna deve estar limpo
    assert "Amostra_1" in resultado.columns
    assert "Amostra_2" in resultado.columns
    
    # O nome do metabólito (índice) deve estar limpo
    assert resultado.index[0] == "Alanine"
    assert resultado.index[1] == "Glucose"
    assert resultado.index.name == "metabolite"


# ==============================================================================
# NOVOS TESTES — Formato Long (Tidy) — adicionado no Sprint 2/4
# ==============================================================================

class TestASICSCleanerLongFormat:
    """
    O ASICSCleaner agora suporta dois formatos de entrada:
      - Wide: index=metabolito, colunas=amostras  (comportamento antigo)
      - Long: colunas Experiment, Metabolite, Concentration_uM_Final

    Esses testes cobrem o novo comportamento de detecção automática.
    """

    @pytest.fixture
    def df_long_formato(self) -> pd.DataFrame:
        """Simula um arquivo ASICS no formato Long (Tidy), sem index_col."""
        return pd.DataFrame({
            "Experiment": ["01RCF", "01RCF", "02RCF"],
            "Metabolite": ["Alanine", "Glucose", "Alanine"],
            "Concentration_uM_Final": [100.5, 200.0, 150.0],
        })

    @pytest.fixture
    def df_long_com_indice(self) -> pd.DataFrame:
        """
        Simula um arquivo ASICS Long lido com index_col=0.
        A coluna 'Experiment' vira o índice — situação real do csv_formatter_runner.
        """
        df = pd.DataFrame({
            "Metabolite": ["Alanine", "Glucose", "Alanine"],
            "Concentration_uM_Final": ["100,5", "200,0", "150,0"],
        }, index=pd.Index(["01RCF", "01RCF", "02RCF"], name="Experiment"))
        return df

    def test_detecta_formato_long_e_mantem_colunas_intactas(self, df_long_formato):
        """O cleaner deve manter as colunas Experiment, Metabolite, Concentration intactas."""
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df_long_formato)

        assert "Experiment" in resultado.columns
        assert "Metabolite" in resultado.columns
        assert "Concentration_uM_Final" in resultado.columns

    def test_detecta_formato_long_quando_experiment_e_indice(self, df_long_com_indice):
        """
        CENÁRIO CRÍTICO: Quando index_col=0 é passado ao reader, 'Experiment'
        se torna o índice. O cleaner deve fazer reset_index para normalizar.
        """
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df_long_com_indice)

        # Após reset_index, 'Experiment' deve voltar a ser coluna
        assert "Experiment" in resultado.columns

    def test_converte_virgula_decimal_para_float(self, df_long_com_indice):
        """
        CENÁRIO: Concentrações com vírgula decimal (padrão pt-BR) devem
        ser convertidas corretamente para float.
        """
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df_long_com_indice)

        assert resultado["Concentration_uM_Final"].dtype == float
        assert resultado["Concentration_uM_Final"].iloc[0] == pytest.approx(100.5)

    def test_limpa_aspas_dos_nomes_de_metabolitos_no_long(self, df_long_formato):
        """Nomes de metabólitos com aspas devem ser limpos mesmo no formato Long."""
        df_com_aspas = df_long_formato.copy()
        df_com_aspas["Metabolite"] = ['"Alanine"', '"Glucose"', '"Alanine"']
        
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df_com_aspas)

        assert "Alanine" in resultado["Metabolite"].values
        assert "Glucose" in resultado["Metabolite"].values
        assert '"Alanine"' not in resultado["Metabolite"].values

    def test_formato_wide_ainda_funciona_apos_mudanca(self):
        """
        REGRESSÃO: Garante que adicionar suporte ao Long não quebrou o Wide.
        """
        df_wide = pd.DataFrame(
            {"S1": [10.5, 5.0], "S2": [8.0, 3.1]},
            index=pd.Index(["Alanine", "Glucose"])
        )
        cleaner = ASICSCleaner()
        resultado = cleaner.clean(df_wide)

        assert resultado.index.name == "metabolite"
        assert "S1" in resultado.columns
        assert resultado.loc["Alanine", "S1"] == pytest.approx(10.5)
