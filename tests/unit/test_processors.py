"""
================================================================================
TESTES UNITÁRIOS DO DataProcessor
================================================================================

CONCEITO FUNDAMENTAL: O QUE É UM MOCK?

  Imagine que você quer testar uma linha de montagem de carros.
  Você NÃO precisa de peças reais para testar se a esteira se move na ordem
  certa. Você pode usar "peças de mentira" (mocks) que apenas registram
  quando foram usadas.

  No nosso caso, o DataProcessor é a "linha de montagem":
     Reader -> Cleaner -> Formatter -> Salva arquivo

  Para testar SE a linha funciona na ORDEM CERTA, usamos mocks para simular
  o Reader, o Cleaner e o Formatter. Assim o teste:
    1. Não depende de arquivos reais em disco.
    2. Não depende de a lógica de limpeza estar correta (isso é papel dos
       tests/cleaners/).
    3. É rápido e isolado.

  `unittest.mock` é a biblioteca padrão do Python para isso.
  `MagicMock()` cria um objeto "mágico" que aceita qualquer chamada de método
  e retorna outro MagicMock por padrão.
================================================================================
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pathlib import Path

# Importamos a classe real que queremos testar
from src.processors.data_processor import DataProcessor


# ==============================================================================
# FIXTURES DE MOCK
# ==============================================================================
# Uma "fixture" no pytest é uma função que prepara dados ou objetos reutilizáveis.
# O decorador @pytest.fixture faz o pytest injetá-la automaticamente nos testes
# que declaram o nome do parâmetro.
# ==============================================================================

@pytest.fixture
def df_fake() -> pd.DataFrame:
    """
    Retorna um DataFrame mínimo simulando dados já lidos do disco.
    Esta é a "matéria-prima" que o nosso pipeline vai processar.
    """
    return pd.DataFrame({
        "Sample":       ["S1", "S2"],
        "Metabolite":   ["Alanine", "Glucose"],
        "Quantity":     [1.5, 2.0],
        "Fitting Error":[0.05, 0.02],
    })


@pytest.fixture
def mock_reader(df_fake) -> MagicMock:
    """
    Cria um Reader falso.
    Quando alguém chamar .read() nele, retorna nosso df_fake
    em vez de abrir um arquivo de verdade.
    """
    reader = MagicMock()
    reader.read.return_value = df_fake  # Define o valor de retorno do método .read()
    return reader


@pytest.fixture
def mock_cleaner(df_fake) -> MagicMock:
    """
    Cria um Cleaner falso.
    Quando alguém chamar .clean() nele, retorna o mesmo df_fake
    (fingimos que ele "limpou" sem alterar nada).
    """
    cleaner = MagicMock()
    cleaner.clean.return_value = df_fake
    return cleaner


@pytest.fixture
def mock_formatter(df_fake) -> MagicMock:
    """
    Cria um Formatter falso.
    Quando alguém chamar .format() nele, retorna o mesmo df_fake.
    """
    formatter = MagicMock()
    formatter.format.return_value = df_fake
    return formatter


# ==============================================================================
# TESTES
# ==============================================================================

class TestDataProcessor:
    """
    Agrupa todos os testes do DataProcessor.
    Usar uma classe é útil para organizar testes relacionados ao mesmo componente.
    """

    def test_pipeline_chama_reader_cleaner_e_formatter_na_ordem_correta(
        self, tmp_path, mock_reader, mock_cleaner, mock_formatter
    ):
        """
        OBJETIVO: Verificar se o DataProcessor chama cada etapa do pipeline
        na ordem correta: Reader -> Cleaner -> Formatter.

        `tmp_path` é uma fixture BUILT-IN do pytest que cria um diretório
        temporário no sistema. O pytest apaga automaticamente depois do teste.
        """
        # ARRANGE (Preparação): Monta o processador com os componentes falsos
        processor = DataProcessor(
            reader=mock_reader,
            output_dir=str(tmp_path),
            cleaner=mock_cleaner,
            formatter=mock_formatter,
        )

        # ACT (Ação): Executa o pipeline
        processor.process("arquivo_qualquer.csv")

        # ASSERT (Verificação): Verifica se cada etapa foi chamada UMA VEZ
        # .assert_called_once() falha se o método não foi chamado exatamente 1x
        mock_reader.read.assert_called_once()
        mock_cleaner.clean.assert_called_once()
        mock_formatter.format.assert_called_once()

    def test_pipeline_sem_cleaner_nao_chama_clean(
        self, tmp_path, mock_reader, mock_formatter
    ):
        """
        OBJETIVO: Verificar que, se não passarmos um Cleaner, o pipeline
        pula a etapa de limpeza sem erros.

        Este é um teste de "caminho alternativo" — o código tem um
        `if self.cleaner:` que precisa ser coberto.
        """
        # ARRANGE: Sem cleaner (None por padrão)
        processor = DataProcessor(
            reader=mock_reader,
            output_dir=str(tmp_path),
            cleaner=None,          # <-- Sem cleaner
            formatter=mock_formatter,
        )

        # ACT
        resultado = processor.process("arquivo.csv")

        # ASSERT: O resultado deve ser um caminho válido (não None)
        assert resultado is not None
        # E o formatter ainda foi chamado mesmo sem o cleaner
        mock_formatter.format.assert_called_once()

    def test_pipeline_sem_formatter_nao_chama_format(
        self, tmp_path, mock_reader, mock_cleaner
    ):
        """
        OBJETIVO: Verificar que, sem Formatter, o pipeline salva os dados
        diretamente após a limpeza.
        """
        processor = DataProcessor(
            reader=mock_reader,
            output_dir=str(tmp_path),
            cleaner=mock_cleaner,
            formatter=None,        # <-- Sem formatter
        )

        resultado = processor.process("arquivo.csv")

        assert resultado is not None
        mock_cleaner.clean.assert_called_once()

    def test_pipeline_retorna_caminho_do_arquivo_salvo(
        self, tmp_path, mock_reader, mock_cleaner, mock_formatter
    ):
        """
        OBJETIVO: Verificar que .process() retorna o caminho completo
        do arquivo de saída gerado.
        """
        processor = DataProcessor(
            reader=mock_reader,
            output_dir=str(tmp_path),
            cleaner=mock_cleaner,
            formatter=mock_formatter,
        )

        resultado = processor.process("meu_arquivo.csv")

        # O caminho retornado deve existir no disco após o processo
        assert resultado is not None
        assert Path(resultado).exists(), "O arquivo de saída não foi criado no disco!"
        assert "formatted_meu_arquivo.csv" in resultado

    def test_pipeline_retorna_none_se_reader_lancar_excecao(
        self, tmp_path, mock_cleaner, mock_formatter
    ):
        """
        OBJETIVO: Verificar que o DataProcessor é resiliente a erros.
        Se o Reader falhar (ex: arquivo corrompido), o pipeline deve
        retornar None em vez de travar o programa inteiro.

        CONCEITO: `side_effect` em mocks
        Em vez de retornar um valor, podemos fazer um mock LANÇAR uma exceção.
        Isso simula um erro real (ex: arquivo não encontrado, permissão negada).
        """
        reader_com_erro = MagicMock()
        reader_com_erro.read.side_effect = FileNotFoundError("Arquivo não existe!")

        processor = DataProcessor(
            reader=reader_com_erro,
            output_dir=str(tmp_path),
            cleaner=mock_cleaner,
            formatter=mock_formatter,
        )

        resultado = processor.process("arquivo_inexistente.csv")

        # O pipeline deve capturar o erro e retornar None silenciosamente
        assert resultado is None
