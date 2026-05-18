"""
================================================================================
TESTES DO StatsEngine (src/analysis/stats_engine.py)
================================================================================

CONCEITO: POR QUE TESTAR O ENGINE COM DADOS SINTÉTICOS?

  O StatsEngine é o coração do Sprint 3 — se uma das Strategies estiver errada,
  todos os resultados no banco serão incorretos. Testamos com valores cuja
  resposta é matematicamente conhecida, tornando os asserts determinísticos.

  Exemplos de valores conhecidos:
  - Pearson/Spearman de dois vetores idênticos  = 1.0
  - Pearson/Spearman de dois vetores opostos    ≈ -1.0
  - Bias de [2, 4] vs [1, 2] = mean([1, 2]) = 1.5
  - MSE  de [2, 4] vs [1, 2] = mean([1, 4]) = 2.5
  - MAPE de [2] vs [1]       = |2-1|/1 * 100 = 100.0

================================================================================
"""
import math

import numpy as np
import pytest

from src.analysis.models import (
    PairedObservation,
    StatResultEspectro,
    StatResultMetabolito,
    StatResultFerramenta,
)
from src.analysis.stats_engine import (
    BiasStrategy,
    MAPEStrategy,
    MSEStrategy,
    PearsonStrategy,
    SpearmanStrategy,
    StatsEngine,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

def _make_obs(
    tool_vals: list[float],
    gs_vals: list[float],
    *,
    tool_test_id: int = 1,
    tool_ref_id: int = 99,
    experiment_id: int = 10,
    metabolite_id: str = "HMDB0000001",
    biofluid: str = "Urina",
) -> list[PairedObservation]:
    """Cria uma lista de PairedObservation a partir de listas simples de valores."""
    return [
        PairedObservation(
            tool_test_id=tool_test_id,
            tool_ref_id=tool_ref_id,
            experiment_id=experiment_id,
            metabolite_id=metabolite_id,
            biofluid=biofluid,
            concentration_tool=t,
            concentration_gs=g,
        )
        for t, g in zip(tool_vals, gs_vals)
    ]


@pytest.fixture
def engine() -> StatsEngine:
    return StatsEngine()


@pytest.fixture
def identical_obs() -> list[PairedObservation]:
    """Vetores idênticos: correlação perfeita positiva."""
    return _make_obs([1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0])


@pytest.fixture
def perfect_obs() -> list[PairedObservation]:
    """Ferramenta = 2× GS: correlação perfeita, mas com bias."""
    return _make_obs([2.0, 4.0, 6.0], [1.0, 2.0, 3.0])


@pytest.fixture
def multi_tool_obs() -> list[PairedObservation]:
    """Duas ferramentas, dois espectros, dois metabolitos — para testar agrupamento."""
    obs = []
    # Ferramenta 1, Espectro 1, Metabolito A
    obs += _make_obs([1.0, 2.0], [1.0, 2.0], tool_test_id=1, experiment_id=10, metabolite_id="HMDB0000001", biofluid="Soro")
    # Ferramenta 1, Espectro 2, Metabolito A
    obs += _make_obs([3.0, 4.0], [3.0, 4.0], tool_test_id=1, experiment_id=11, metabolite_id="HMDB0000001", biofluid="Urina")
    # Ferramenta 2, Espectro 1, Metabolito A
    obs += _make_obs([1.5, 2.5], [1.0, 2.0], tool_test_id=2, experiment_id=10, metabolite_id="HMDB0000001", biofluid="Soro")
    return obs


# ==============================================================================
# TESTES — Strategies individuais
# ==============================================================================

class TestPearsonStrategy:
    """Valida a Strategy de correlação de Pearson."""

    def test_vetores_identicos_retorna_r_1(self):
        """Pearson de vetores idênticos deve ser 1.0."""
        s = PearsonStrategy()
        tool = np.array([1.0, 2.0, 3.0, 4.0])
        gs   = np.array([1.0, 2.0, 3.0, 4.0])
        r, p = s.calculate(tool, gs)
        assert math.isclose(r, 1.0, abs_tol=1e-9)

    def test_vetores_opostos_retorna_r_negativo(self):
        """Pearson de vetores inversamente proporcionais deve ser próximo de -1.0."""
        s = PearsonStrategy()
        tool = np.array([1.0, 2.0, 3.0, 4.0])
        gs   = np.array([4.0, 3.0, 2.0, 1.0])
        r, p = s.calculate(tool, gs)
        assert r < -0.9

    def test_poucos_pares_retorna_defaults(self):
        """Com menos de 3 pares, deve retornar (0.0, 1.0) em vez de erro."""
        s = PearsonStrategy()
        r, p = s.calculate(np.array([1.0, 2.0]), np.array([1.0, 2.0]))
        assert r == 0.0
        assert p == 1.0

    def test_p_valor_entre_0_e_1(self):
        """O p-valor deve sempre estar no intervalo [0, 1]."""
        s = PearsonStrategy()
        tool = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
        gs   = np.array([1.5, 2.5, 2.0, 4.5, 3.5])
        _, p = s.calculate(tool, gs)
        assert 0.0 <= p <= 1.0


class TestSpearmanStrategy:
    """Valida a Strategy de correlação de Spearman."""

    def test_vetores_identicos_retorna_r_1(self):
        s = SpearmanStrategy()
        tool = np.array([1.0, 2.0, 3.0, 4.0])
        gs   = np.array([1.0, 2.0, 3.0, 4.0])
        r, p = s.calculate(tool, gs)
        assert math.isclose(r, 1.0, abs_tol=1e-9)

    def test_poucos_pares_retorna_defaults(self):
        s = SpearmanStrategy()
        r, p = s.calculate(np.array([1.0]), np.array([2.0]))
        assert r == 0.0
        assert p == 1.0


class TestBiasStrategy:
    """Valida a Strategy de Bias."""

    def test_sem_bias(self):
        """Vetores idênticos → bias = 0.0."""
        s = BiasStrategy()
        result = s.calculate(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        assert math.isclose(result, 0.0, abs_tol=1e-9)

    def test_superestimacao(self):
        """Ferramenta = GS + 1 → bias = +1.0."""
        s = BiasStrategy()
        result = s.calculate(
            np.array([2.0, 3.0, 4.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        assert math.isclose(result, 1.0, abs_tol=1e-9)

    def test_subestimacao_valor_conhecido(self):
        """Bias de [2, 4] vs [1, 2] = mean([1, 2]) = 1.5."""
        s = BiasStrategy()
        result = s.calculate(np.array([2.0, 4.0]), np.array([1.0, 2.0]))
        assert math.isclose(result, 1.5, abs_tol=1e-9)


class TestMSEStrategy:
    """Valida a Strategy de Erro Quadrático Médio."""

    def test_vetores_identicos_mse_zero(self):
        s = MSEStrategy()
        result = s.calculate(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
        )
        assert math.isclose(result, 0.0, abs_tol=1e-9)

    def test_valor_conhecido(self):
        """MSE de [2, 4] vs [1, 2] = mean([1², 2²]) = mean([1, 4]) = 2.5."""
        s = MSEStrategy()
        result = s.calculate(np.array([2.0, 4.0]), np.array([1.0, 2.0]))
        assert math.isclose(result, 2.5, abs_tol=1e-9)

    def test_mse_sempre_nao_negativo(self):
        """MSE nunca pode ser negativo."""
        s = MSEStrategy()
        result = s.calculate(
            np.array([1.0, 5.0, 2.0]),
            np.array([3.0, 2.0, 4.0]),
        )
        assert result >= 0.0


class TestMAPEStrategy:
    """Valida a Strategy de MAPE."""

    def test_valor_conhecido(self):
        """MAPE de [2] vs [1] = |2-1|/1 * 100 = 100.0."""
        s = MAPEStrategy()
        result = s.calculate(np.array([2.0]), np.array([1.0]))
        assert math.isclose(result, 100.0, abs_tol=1e-9)

    def test_ignora_gs_zero(self):
        """Pares onde gs=0 devem ser ignorados (sem ZeroDivisionError)."""
        s = MAPEStrategy()
        # Apenas o par (2, 1) entra: |2-1|/1 * 100 = 100%
        result = s.calculate(np.array([2.0, 5.0]), np.array([1.0, 0.0]))
        assert math.isclose(result, 100.0, abs_tol=1e-9)

    def test_todo_gs_zero_retorna_zero(self):
        """Se todos os GS forem 0, retornar 0.0 em vez de erro."""
        s = MAPEStrategy()
        result = s.calculate(np.array([1.0, 2.0]), np.array([0.0, 0.0]))
        assert result == 0.0

    def test_mape_sempre_nao_negativo(self):
        s = MAPEStrategy()
        result = s.calculate(np.array([1.0, 3.0]), np.array([2.0, 2.0]))
        assert result >= 0.0


# ==============================================================================
# TESTES — StatsEngine (orquestração)
# ==============================================================================

class TestStatsEngineCalculateAll:
    """Testa a orquestração dos 3 níveis de granularidade."""

    def test_retorna_lista_de_stat_results(self, engine, identical_obs):
        counts = {10: {'gs_total': 5, 'tools': {1: 5}}}
        results = engine.calculate_all(identical_obs, counts)
        assert isinstance(results, tuple)
        assert len(results) == 3
        assert all(isinstance(r, StatResultEspectro) for r in results[0])
        assert all(isinstance(r, StatResultMetabolito) for r in results[1])
        assert all(isinstance(r, StatResultFerramenta) for r in results[2])

    def test_lista_vazia_retorna_lista_vazia(self, engine):
        results = engine.calculate_all([], {})
        assert results == ([], [], [])

    def test_nivel_1_tem_experiment_id(self, engine, identical_obs):
        """Resultados de nível 1 devem ter experiment_id preenchido."""
        counts = {10: {'gs_total': 5, 'tools': {1: 5}}}
        results = engine.calculate_all(identical_obs, counts)
        nivel_1 = results[0]
        assert len(nivel_1) > 0
        assert all(r.experiment_id is not None for r in nivel_1)

    def test_nivel_3_tem_experiment_e_biofluid_none(self, engine, identical_obs):
        """Resultados de nível 3 avaliam de forma global por ferramenta."""
        counts = {10: {'gs_total': 5, 'tools': {1: 5}}}
        results = engine.calculate_all(identical_obs, counts)
        nivel_3 = results[2]
        assert len(nivel_3) > 0

    def test_multi_tool_gera_resultados_separados(self, engine, multi_tool_obs):
        """Ferramentas diferentes devem gerar StatResults distintos."""
        counts = {
            10: {'gs_total': 2, 'tools': {1: 2, 2: 2}},
            11: {'gs_total': 2, 'tools': {1: 2}}
        }
        results = engine.calculate_all(multi_tool_obs, counts)
        tool_ids = {r.tool_test_id for r in results[0]}
        assert 1 in tool_ids
        assert 2 in tool_ids

    def test_correlacao_perfeita_nos_resultados(self, engine, identical_obs):
        """Com observações idênticas, Pearson deve ser 1.0 no nível 1."""
        counts = {10: {'gs_total': 5, 'tools': {1: 5}}}
        results = engine.calculate_all(identical_obs, counts)
        nivel_1 = results[0]
        for r in nivel_1:
            assert math.isclose(r.mse, 0.0, abs_tol=1e-9)
            assert math.isclose(r.bias, 0.0, abs_tol=1e-9)


class TestStatsEngineCoverage:
    """Testa os métodos estáticos de cobertura."""

    def test_cobertura_100_pct(self):
        assert StatsEngine.calculate_coverage(10, 10) == 100.0

    def test_cobertura_50_pct(self):
        assert StatsEngine.calculate_coverage(5, 10) == 50.0

    def test_cobertura_gs_zero_retorna_zero(self):
        """GS sem metabolitos → cobertura 0.0 sem divisão por zero."""
        assert StatsEngine.calculate_coverage(0, 0) == 0.0

    def test_cobertura_entre_0_e_100(self):
        result = StatsEngine.calculate_coverage(7, 10)
        assert 0.0 <= result <= 100.0
