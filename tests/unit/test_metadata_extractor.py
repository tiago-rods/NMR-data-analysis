"""
================================================================================
TESTES DO MetadataExtractor (src/ingestion/metadata_extractor.py)
================================================================================

CONCEITO: POR QUE TESTAR O EXTRATOR DE METADADOS?

  O MetadataExtractor usa Regex para interpretar o nome dos arquivos CSV.
  Ele é o ponto de entrada do motor de ingestão — se ele extrair a ferramenta
  ou a frequência errada, toda a ingestão vai para o banco de forma errada.

  Nomes de arquivo podem ter variações sutis entre experimentos. Esses testes
  garantem que o extrator é resiliente a todas as variações conhecidas.

================================================================================
"""
import pytest
from src.ingestion.metadata_extractor import MetadataExtractor, ExperimentMetadata


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def extractor() -> MetadataExtractor:
    return MetadataExtractor()


# ==============================================================================
# TESTES — Arquivos de ferramentas padrão
# ==============================================================================

class TestMetadataExtractorArquivosPadrao:
    """Testa a extração de metadados dos nomes de arquivo no padrão do projeto."""

    @pytest.mark.parametrize("filename, expected_id, expected_freq, expected_tool, expected_bio, expected_fab", [
        (
            "formatted_LNBio18_Bruker_600MHz_Urina_nmRanalysis_csv_size180_quantification.csv",
            "LNBio18", 600.0, "nmRanalysis", "Urina", "Bruker"
        ),
        (
            "formatted_LNBio24_Bruker_600MHz_ASICS_Urina_fid_size180.csv",
            "LNBio24", 600.0, "ASICS", "Urina", "Bruker"
        ),
        (
            "formatted_LNBio12_Bruker_600MHz_MagMet_Urina_size90.csv",
            "LNBio12", 600.0, "MagMet", "Urina", "Bruker"
        ),
        (
            "formatted_LNBio05_Agilent_500MHz_ASICS_Soro_fid_size60.csv",
            "LNBio05", 500.0, "ASICS", "Soro", "Agilent"
        ),
    ], ids=["nmRanalysis", "asics-fid", "magmet", "asics-soro"])
    def test_extrai_campos_principais(
        self, extractor, filename, expected_id, expected_freq,
        expected_tool, expected_bio, expected_fab
    ):
        """
        CENÁRIO PARAMETRIZADO: Verifica que os campos principais são extraídos
        corretamente para os principais formatos de nome de arquivo.
        """
        meta = extractor.extract(filename)

        assert meta is not None, f"Extrator retornou None para: {filename}"
        assert meta.id_experimento == expected_id
        assert meta.frequencia == expected_freq
        assert meta.ferramenta == expected_tool
        assert meta.biofluido == expected_bio
        assert meta.fabricante == expected_fab

    def test_independencia_de_ordem_no_nome(self, extractor):
        """
        CENÁRIO: O extrator não deve depender da ordem dos termos (LNBio, MHz, Tool).
        Invertemos a ordem padrão para garantir robustez.
        """
        filename = "nmRanalysis_Urina_600MHz_Bruker_LNBio18_size180.csv"
        meta = extractor.extract(filename)
        
        assert meta is not None
        assert meta.id_experimento == "LNBio18"
        assert meta.frequencia == 600.0
        assert meta.ferramenta == "nmRanalysis"

    def test_extrai_tamanho_da_amostra(self, extractor):
        """O tamanho (número de espectros) deve ser extraído como inteiro."""
        meta = extractor.extract("formatted_LNBio18_Bruker_600MHz_Urina_nmRanalysis_csv_size180.csv")
        assert meta is not None
        assert meta.tamanho == 180

    def test_infere_tecnologia_fid(self, extractor):
        """Arquivos com 'fid' no nome devem ter tecnologia='fid'."""
        meta = extractor.extract("formatted_LNBio24_Bruker_600MHz_ASICS_Urina_fid_size180.csv")
        assert meta is not None
        assert meta.tecnologia == "fid"

    def test_infere_tecnologia_csv(self, extractor):
        """Arquivos com 'csv' no nome devem ter tecnologia='csv'."""
        meta = extractor.extract("formatted_LNBio18_Bruker_600MHz_nmRanalysis_Urina_csv_size180.csv")
        assert meta is not None
        assert meta.tecnologia == "csv"


# ==============================================================================
# TESTES — Arquivos Gold Standard
# ==============================================================================

class TestMetadataExtractorGoldStandard:
    """
    Testa que o extrator retorna None para arquivos Gold Standard,
    já que esses não possuem frequência, ferramenta ou tamanho no nome.
    """

    @pytest.mark.parametrize("filename", [
        "LNBioGS_Urina.csv",
        "LNBioGS_Soro.csv",
    ], ids=["gs-urina", "gs-soro"])
    def test_retorna_none_para_arquivo_gold_standard(self, extractor, filename):
        """
        CENÁRIO: Arquivos Gold Standard não seguem o padrão de nomenclatura
        completo. O extrator deve retornar None (sem quebrar) para que o
        orquestrador possa tratá-los separadamente.
        """
        meta = extractor.extract(filename)
        assert meta is None, f"Esperava None para '{filename}', mas recebeu: {meta}"


# ==============================================================================
# TESTES — Entradas inválidas e casos de borda
# ==============================================================================

class TestMetadataExtractorCasosDeBorda:
    """Testa o comportamento do extrator com nomes de arquivo inválidos."""

    def test_retorna_none_para_nome_sem_frequencia(self, extractor):
        """Sem 'NNNMHz', o extrator não consegue extrair a frequência → None."""
        meta = extractor.extract("formatted_LNBio18_Bruker_Urina_nmRanalysis_size180.csv")
        assert meta is None

    def test_retorna_none_para_nome_sem_id_lnbio(self, extractor):
        """Sem 'LNBioNN', o extrator não consegue identificar o experimento → None."""
        meta = extractor.extract("formatted_Bruker_600MHz_Urina_nmRanalysis_size180.csv")
        assert meta is None

    def test_retorna_none_para_nome_sem_tamanho(self, extractor):
        """Sem 'sizeNN', o extrator não consegue saber o tamanho → None."""
        meta = extractor.extract("formatted_LNBio18_Bruker_600MHz_Urina_nmRanalysis.csv")
        assert meta is None

    def test_retorna_none_para_string_vazia(self, extractor):
        """Uma string vazia não deve levantar exceção — deve retornar None."""
        meta = extractor.extract("")
        assert meta is None

    def test_retorna_dataclass_valida(self, extractor):
        """O retorno para um arquivo válido deve ser uma instância de ExperimentMetadata."""
        meta = extractor.extract("formatted_LNBio18_Bruker_600MHz_Urina_nmRanalysis_csv_size180.csv")
        assert isinstance(meta, ExperimentMetadata)

    def test_fabricante_desconhecido_quando_ausente(self, extractor):
        """Se o fabricante não estiver no nome, deve ser 'Unknown'."""
        meta = extractor.extract("formatted_LNBio18_600MHz_Urina_nmRanalysis_csv_size180.csv")
        if meta is not None:
            assert meta.fabricante == "Unknown"
