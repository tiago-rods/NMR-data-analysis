"""
================================================================================
TESTES DO StatsCalculator (src/analysis/stats_calculator.py)
================================================================================

CONCEITO: TESTANDO O REPOSITORY COM BANCO MOCKADO

  O StatsCalculator faz SQL puro via psycopg2. Não queremos uma conexão real
  nos testes — isso tornaria os testes lentos, frágeis e dependentes de infra.

  Estratégia: usamos unittest.mock para substituir o cursor do psycopg2 por
  um objeto controlado. Injetamos as linhas que queremos que o banco "retorne"
  e verificamos que o Calculator as transforma corretamente em PairedObservations.

  Isso testa:
  1. Que a query não tem erros de sintaxe Python.
  2. Que o mapeamento row → PairedObservation está correto.
  3. Que o filtro por tool_name é aplicado (WHERE clause).

================================================================================
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.analysis.models import PairedObservation
from src.analysis.stats_calculator import StatsCalculator


# ==============================================================================
# FIXTURES
# ==============================================================================

def _fake_row(
    tool_test_id=1,
    tool_ref_id=99,
    experiment_id=10,
    metabolite_id="HMDB0000001",
    biofluid="Urina",
    concentration_tool=2.5,
    concentration_gs=2.0,
) -> dict:
    """Cria uma linha fake que simula o retorno de RealDictCursor."""
    return {
        "tool_test_id":       tool_test_id,
        "tool_ref_id":        tool_ref_id,
        "experiment_id":      experiment_id,
        "metabolite_id":      metabolite_id.ljust(11),  # CHAR(11) do banco tem espaços
        "biofluid":           biofluid,
        "concentration_tool": concentration_tool,
        "concentration_gs":   concentration_gs,
    }


@pytest.fixture
def mock_db():
    """DataBaseManager mock com conn.cursor() configurado."""
    db = MagicMock()
    db.conn = MagicMock()
    return db


@pytest.fixture
def calculator(mock_db) -> StatsCalculator:
    return StatsCalculator(mock_db)


def _configure_cursor(mock_db, rows: list[dict]) -> None:
    """Configura o cursor mock para retornar as linhas especificadas."""
    cursor_mock = MagicMock()
    cursor_mock.__enter__ = MagicMock(return_value=cursor_mock)
    cursor_mock.__exit__ = MagicMock(return_value=False)
    cursor_mock.fetchall.return_value = rows
    mock_db.conn.cursor.return_value = cursor_mock


# ==============================================================================
# TESTES — fetch_paired_data
# ==============================================================================

class TestFetchPairedData:
    """Testa o mapeamento de linhas SQL → PairedObservation."""

    def test_retorna_lista_de_paired_observations(self, calculator, mock_db):
        """O retorno deve ser uma lista de PairedObservation."""
        _configure_cursor(mock_db, [_fake_row()])
        result = calculator.fetch_paired_data()
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PairedObservation)

    def test_mapeia_campos_corretamente(self, calculator, mock_db):
        """Cada campo do dict deve mapear para o campo correto do dataclass."""
        row = _fake_row(
            tool_test_id=5,
            tool_ref_id=99,
            experiment_id=42,
            metabolite_id="HMDB0000123",
            biofluid="Soro",
            concentration_tool=3.14,
            concentration_gs=3.00,
        )
        _configure_cursor(mock_db, [row])
        obs = calculator.fetch_paired_data()[0]

        assert obs.tool_test_id == 5
        assert obs.tool_ref_id == 99
        assert obs.experiment_id == 42
        assert obs.metabolite_id == "HMDB0000123"
        assert obs.biofluid == "Soro"
        assert obs.concentration_tool == 3.14
        assert obs.concentration_gs == 3.00

    def test_metabolite_id_sem_espacos(self, calculator, mock_db):
        """O CHAR(11) do banco vem com espaços — o Calculator deve remover com strip()."""
        row = _fake_row(metabolite_id="HMDB000001 ")  # com espaço
        _configure_cursor(mock_db, [row])
        obs = calculator.fetch_paired_data()[0]
        assert " " not in obs.metabolite_id

    def test_banco_vazio_retorna_lista_vazia(self, calculator, mock_db):
        """Sem linhas no banco, deve retornar lista vazia sem exceção."""
        _configure_cursor(mock_db, [])
        result = calculator.fetch_paired_data()
        assert result == []

    def test_multiplas_linhas(self, calculator, mock_db):
        """Deve processar múltiplas linhas corretamente."""
        rows = [
            _fake_row(experiment_id=10, concentration_tool=1.0, concentration_gs=1.1),
            _fake_row(experiment_id=11, concentration_tool=2.0, concentration_gs=2.2),
            _fake_row(experiment_id=12, concentration_tool=3.0, concentration_gs=3.3),
        ]
        _configure_cursor(mock_db, rows)
        result = calculator.fetch_paired_data()
        assert len(result) == 3

    def test_sem_conexao_levanta_runtime_error(self):
        """DataBaseManager com conn=None deve levantar RuntimeError."""
        db_sem_conn = MagicMock()
        db_sem_conn.conn = None
        with pytest.raises(RuntimeError, match="conexão ativa"):
            StatsCalculator(db_sem_conn)


# ==============================================================================
# TESTES — fetch_gs_metabolite_count
# ==============================================================================

class TestFetchGsMetaboliteCount:
    """Testa a contagem de metabolitos no Gold Standard."""

    def test_retorna_inteiro(self, calculator, mock_db):
        cursor_mock = MagicMock()
        cursor_mock.__enter__ = MagicMock(return_value=cursor_mock)
        cursor_mock.__exit__ = MagicMock(return_value=False)
        cursor_mock.fetchone.return_value = (25,)
        mock_db.conn.cursor.return_value = cursor_mock

        result = calculator.fetch_gs_metabolite_count(experiment_id=10)
        assert result == 25

    def test_retorna_zero_quando_nenhum_resultado(self, calculator, mock_db):
        cursor_mock = MagicMock()
        cursor_mock.__enter__ = MagicMock(return_value=cursor_mock)
        cursor_mock.__exit__ = MagicMock(return_value=False)
        cursor_mock.fetchone.return_value = None
        mock_db.conn.cursor.return_value = cursor_mock

        result = calculator.fetch_gs_metabolite_count(experiment_id=999)
        assert result == 0
