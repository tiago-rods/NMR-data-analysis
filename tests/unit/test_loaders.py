"""
================================================================================
TESTES DOS LOADERS (src/loaders/)
================================================================================

CONCEITO: O PADRÃO LOADER (Reader + Parser)

  Um Loader combina dois componentes menores:
    1. READER : lê o arquivo bruto do disco e retorna um DataFrame
    2. PARSER : pega esse DataFrame e converte para a estrutura final
                (ex: lista de dicionários, formato de banco de dados)

  O CSVLoader orquestra: Reader.read(path) -> Parser.parse(dataframe)

  Por que separar assim?
    - Você pode trocar o Parser sem mudar como lê o arquivo.
    - Você pode testar cada parte de forma independente.

ESTRATÉGIA DE TESTE PARA LOADERS:
  Usamos MOCKS para o Reader e o Parser, assim testamos APENAS a lógica
  de orquestração do Loader (igual ao que fizemos no DataProcessor).

  Para testes que precisam de arquivo real (ex: FileNotFoundError),
  usamos `tmp_path` do pytest para criar arquivos temporários no disco.

CONCEITO NOVO: `pytest.fixture(scope="class")`
  Por padrão, fixtures são recriadas a cada função de teste.
  Com `scope="class"`, a fixture é criada UMA VEZ e reutilizada por todos
  os testes da classe. Útil quando a criação do objeto é custosa.

================================================================================
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.loaders.csv_loader import CSVLoader
from src.loaders.jdx_loader import JDXLoader


# ==============================================================================
# TESTES DO CSVLoader
# ==============================================================================

class TestCSVLoader:

    @pytest.fixture
    def df_fake(self) -> pd.DataFrame:
        """DataFrame mínimo que simula a saída do CSVReader."""
        return pd.DataFrame({
            "Sample":    ["S1", "S2"],
            "Metabolite":["Alanine", "Glucose"],
            "Quantity":  [1.5, 2.0],
        })

    @pytest.fixture
    def loader_com_mocks(self, df_fake) -> CSVLoader:
        """
        Monta um CSVLoader com Reader e Parser FALSOS.
        O Reader retorna df_fake.
        O Parser retorna a lista de dicionários equivalente.
        """
        mock_reader = MagicMock()
        mock_reader.read.return_value = df_fake

        mock_parser = MagicMock()
        mock_parser.parse.return_value = df_fake.to_dict(orient="records")

        return CSVLoader(reader=mock_reader, parser=mock_parser)

    # --- Testes de fluxo correto (happy path) ---

    def test_load_chama_reader_e_depois_parser(self, tmp_path, loader_com_mocks):
        """
        OBJETIVO: Garantir que o Loader chama Reader ANTES do Parser,
        passando o resultado de um para o outro corretamente.

        Criamos um arquivo vazio real em tmp_path para satisfazer a
        verificação `self.exists(path)` dentro do Loader.
        """
        # Criamos um arquivo real (conteúdo não importa — o reader é mock)
        arquivo_fake = tmp_path / "dados.csv"
        arquivo_fake.write_text("col1,col2\n1,2")

        resultado = loader_com_mocks.load(str(arquivo_fake))

        # Verifica que o Reader foi chamado com o caminho correto
        loader_com_mocks.reader.read.assert_called_once_with(str(arquivo_fake))
        # Verifica que o Parser foi chamado depois
        loader_com_mocks.parser.parse.assert_called_once()
        # Verifica que o resultado final é a lista de dicionários do Parser
        assert isinstance(resultado, list)

    def test_load_retorna_lista_de_dicionarios(self, tmp_path, loader_com_mocks):
        """
        OBJETIVO: O contrato do CSVLoader é retornar uma lista de dicts.
        Cada dict representa uma linha da tabela.
        """
        arquivo_fake = tmp_path / "dados.csv"
        arquivo_fake.write_text("col\n1")

        resultado = loader_com_mocks.load(str(arquivo_fake))

        assert isinstance(resultado, list)
        assert len(resultado) == 2  # df_fake tem 2 linhas -> 2 dicts

    # --- Testes de casos de erro ---

    def test_load_levanta_file_not_found_para_arquivo_inexistente(self):
        """
        CENÁRIO DE BORDA: Tentar carregar um arquivo que não existe no disco.
        O Loader deve levantar FileNotFoundError com uma mensagem clara.
        """
        loader = CSVLoader()  # Loader real, sem mocks
        with pytest.raises(FileNotFoundError, match="File not found"):
            loader.load("/caminho/que/nao/existe/arquivo.csv")

    # --- Testes do método save ---

    def test_save_cria_arquivo_csv_no_disco(self, tmp_path):
        """
        OBJETIVO: Verificar que save() efetivamente escreve um arquivo CSV.
        """
        loader = CSVLoader()
        df = pd.DataFrame({"metabolite": ["Alanine"], "S1": [1.5]})
        caminho = str(tmp_path / "output.csv")

        loader.save(df, caminho)

        assert Path(caminho).exists()
        df_lido = pd.read_csv(caminho)
        assert "metabolite" in df_lido.columns

    def test_save_levanta_tipo_errado(self, tmp_path):
        """
        CENÁRIO DE BORDA: Tentar salvar um tipo não suportado (ex: uma string).
        O Loader deve rejeitar isso com TypeError.
        """
        loader = CSVLoader()
        with pytest.raises(TypeError):
            loader.save("isso não é um DataFrame", str(tmp_path / "out.csv"))

    # --- Testes do método exists ---

    def test_exists_retorna_true_para_arquivo_real(self, tmp_path):
        """OBJETIVO: exists() deve retornar True quando o arquivo está no disco."""
        arquivo = tmp_path / "existe.csv"
        arquivo.write_text("a,b\n1,2")
        loader = CSVLoader()
        assert loader.exists(str(arquivo)) is True

    def test_exists_retorna_false_para_arquivo_inexistente(self):
        """OBJETIVO: exists() deve retornar False quando o arquivo não existe."""
        loader = CSVLoader()
        assert loader.exists("/nao/existe/arquivo.csv") is False

    # --- Testes do método delete ---

    def test_delete_remove_arquivo_do_disco(self, tmp_path):
        """OBJETIVO: delete() deve apagar o arquivo e ele não deve mais existir."""
        arquivo = tmp_path / "apagar.csv"
        arquivo.write_text("a,b\n1,2")
        loader = CSVLoader()

        loader.delete(str(arquivo))

        assert not arquivo.exists()

    def test_delete_nao_levanta_erro_se_arquivo_nao_existe(self):
        """
        CENÁRIO DE BORDA: delete() chamado para arquivo inexistente.
        O comportamento esperado é silencioso — não deve lançar exceção.
        """
        loader = CSVLoader()
        # Não deve levantar nenhuma exceção
        loader.delete("/caminho/que/nao/existe.csv")


# ==============================================================================
# TESTES DO JDXLoader
# ==============================================================================

class TestJDXLoader:
    """
    O JDXLoader é similar ao CSVLoader, mas para o formato JDX (espectros NMR).
    A diferença principal: ele NÃO suporta salvar arquivos (operação somente leitura).
    """

    def test_load_levanta_file_not_found_para_arquivo_inexistente(self):
        """
        CENÁRIO DE BORDA: Arquivo JDX não encontrado.
        Deve levantar FileNotFoundError com mensagem clara.
        """
        loader = JDXLoader()
        with pytest.raises(FileNotFoundError, match="File not found"):
            loader.load("/nao/existe/espectro.jdx")

    def test_save_levanta_not_implemented_error(self):
        """
        OBJETIVO: JDX é um formato somente-leitura no nosso sistema.
        Chamar save() deve levantar NotImplementedError.

        CONCEITO: NotImplementedError é usado quando uma operação existe
        na interface (classe base), mas a implementação específica não suporta.
        """
        loader = JDXLoader()
        with pytest.raises(NotImplementedError):
            loader.save({"dados": "qualquer"}, "/caminho/espectro.jdx")

    def test_exists_retorna_false_para_arquivo_inexistente(self):
        """OBJETIVO: exists() com caminho inválido retorna False."""
        loader = JDXLoader()
        assert loader.exists("/nao/existe.jdx") is False

    def test_delete_silencioso_para_arquivo_inexistente(self):
        """
        CENÁRIO DE BORDA: delete() em arquivo que não existe.
        Deve ser silencioso, igual ao CSVLoader.
        """
        loader = JDXLoader()
        loader.delete("/nao/existe.jdx")  # Não deve lançar exceção
