"""
StatsEngine — Strategy Pattern.

Responsabilidade única: calcular métricas estatísticas a partir de
PairedObservations. Nenhum acesso ao banco de dados aqui.

Estrutura:
  MetricStrategy (ABC)       ← interface de cada métrica
    ├── PearsonStrategy
    ├── SpearmanStrategy
    ├── BiasStrategy
    ├── MSEStrategy
    └── MAPEStrategy

  StatsEngine                ← orquestra o cálculo nos 3 níveis de granularidade
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import groupby
from typing import Optional

import numpy as np
import scipy.stats

from src.analysis.models import PairedObservation, StatResult

logger = logging.getLogger(__name__)

# Número mínimo de pares para calcular métricas de correlação.
# Com menos pares, os coeficientes não têm significância estatística.
_MIN_PAIRS = 3


# ── Strategies ────────────────────────────────────────────────────────────────

class MetricStrategy(ABC):
    """Interface Strategy: cada subclasse implementa uma métrica específica."""

    @abstractmethod
    def calculate(
        self, tool: np.ndarray, gs: np.ndarray
    ) -> float | tuple[float, float]:
        """
        Calcula a métrica entre os vetores tool e gs.

        Returns:
            float único ou (coeficiente, p-valor) dependendo da métrica.
        """
        ...


class PearsonStrategy(MetricStrategy):
    """Correlação de Pearson — mede associação linear."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> tuple[float, float]:
        if len(tool) < _MIN_PAIRS:
            return 0.0, 1.0
        r, p = scipy.stats.pearsonr(tool, gs)
        return float(r), float(p)


class SpearmanStrategy(MetricStrategy):
    """Correlação de Spearman — mede associação monotônica (robusta a outliers)."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> tuple[float, float]:
        if len(tool) < _MIN_PAIRS:
            return 0.0, 1.0
        r, p = scipy.stats.spearmanr(tool, gs)
        return float(r), float(p)


class BiasStrategy(MetricStrategy):
    """Viés médio: mean(tool − gs). Positivo → superestimação; negativo → subestimação."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        return float(np.mean(tool - gs))


class MSEStrategy(MetricStrategy):
    """Erro Quadrático Médio — penaliza erros grandes."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        return float(np.mean((tool - gs) ** 2))


class MAPEStrategy(MetricStrategy):
    """
    Erro Percentual Absoluto Médio.
    Ignora pares onde gs == 0 para evitar divisão por zero.
    """

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        mask = gs != 0
        if not np.any(mask):
            return 0.0
        return float(np.mean(np.abs((tool[mask] - gs[mask]) / gs[mask])) * 100)


# ── Engine ─────────────────────────────────────────────────────────────────────

class StatsEngine:
    """
    Orquestra o cálculo de métricas nos 3 níveis de granularidade:

    Nível 1 — Por espectro:
        experiment_id preenchido, biofluid preenchido.
        → Alimenta analise_comparativa + metricas.

    Nível 2 — Por ferramenta + biofluido:
        experiment_id=None, biofluid preenchido.
        → Alimenta metricas (agregado por biofluido).

    Nível 3 — Por ferramenta (total):
        experiment_id=None, biofluid=None.
        → Alimenta metricas (agregado geral).

    Design Pattern: Strategy — as métricas são injetadas no construtor,
    permitindo substituir ou adicionar métricas sem alterar o Engine.
    """

    def __init__(self, strategies: list[MetricStrategy] | None = None):
        self._pearson  = PearsonStrategy()
        self._spearman = SpearmanStrategy()
        self._strategies: list[MetricStrategy] = strategies or [
            BiasStrategy(),
            MSEStrategy(),
            MAPEStrategy(),
        ]

    # ── API pública ────────────────────────────────────────────────────────────

    def calculate_all(
        self, observations: list[PairedObservation]
    ) -> list[StatResult]:
        """
        Calcula métricas nos 3 níveis e retorna a lista completa de StatResults.
        """
        results: list[StatResult] = []
        results.extend(self._by_experiment(observations))        # nível 1
        results.extend(self._by_tool_and_biofluid(observations)) # nível 2
        results.extend(self._by_tool(observations))              # nível 3

        logger.info(
            "calculate_all: %d StatResults gerados (%d obs de entrada).",
            len(results),
            len(observations),
        )
        return results

    # ── Nível 1: por espectro ──────────────────────────────────────────────────

    def _by_experiment(
        self, observations: list[PairedObservation]
    ) -> list[StatResult]:
        """Agrupa por (tool_test_id, tool_ref_id, experiment_id, metabolite_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id, o.experiment_id, o.metabolite_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id, experiment_id, metabolite_id = key
            obs_list = list(group)
            biofluid = obs_list[0].biofluid

            result = self._compute_stat_result(
                obs_list,
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                metabolite_id=metabolite_id,
                experiment_id=experiment_id,
                biofluid=biofluid,
            )
            results.append(result)

        return results

    # ── Nível 2: por ferramenta + biofluido ────────────────────────────────────

    def _by_tool_and_biofluid(
        self, observations: list[PairedObservation]
    ) -> list[StatResult]:
        """Agrupa por (tool_test_id, tool_ref_id, biofluid, metabolite_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id, o.biofluid, o.metabolite_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id, biofluid, metabolite_id = key
            obs_list = list(group)

            result = self._compute_stat_result(
                obs_list,
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                metabolite_id=metabolite_id,
                experiment_id=None,   # agregado → sem espectro específico
                biofluid=biofluid,
            )
            results.append(result)

        return results

    # ── Nível 3: por ferramenta (total) ───────────────────────────────────────

    def _by_tool(
        self, observations: list[PairedObservation]
    ) -> list[StatResult]:
        """Agrupa por (tool_test_id, tool_ref_id, metabolite_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id, o.metabolite_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id, metabolite_id = key
            obs_list = list(group)

            result = self._compute_stat_result(
                obs_list,
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                metabolite_id=metabolite_id,
                experiment_id=None,  # agregado total
                biofluid=None,
            )
            results.append(result)

        return results

    # ── Núcleo de cálculo ──────────────────────────────────────────────────────

    def _compute_stat_result(
        self,
        obs: list[PairedObservation],
        *,
        tool_test_id: int,
        tool_ref_id: int,
        metabolite_id: str,
        experiment_id: Optional[int],
        biofluid: Optional[str],
    ) -> StatResult:
        """
        Aplica todas as estratégias a um grupo de observações e retorna um StatResult.
        """
        tool_arr = np.array([o.concentration_tool for o in obs], dtype=float)
        gs_arr   = np.array([o.concentration_gs   for o in obs], dtype=float)

        pearson_r,  pearson_p  = self._pearson.calculate(tool_arr, gs_arr)
        spearman_r, spearman_p = self._spearman.calculate(tool_arr, gs_arr)

        bias = BiasStrategy().calculate(tool_arr, gs_arr)
        mse  = MSEStrategy().calculate(tool_arr, gs_arr)
        mape = MAPEStrategy().calculate(tool_arr, gs_arr)

        return StatResult(
            tool_test_id=tool_test_id,
            tool_ref_id=tool_ref_id,
            metabolite_id=metabolite_id,
            experiment_id=experiment_id,
            biofluid=biofluid,
            pearson_r=pearson_r,
            pearson_p=pearson_p,
            spearman_r=spearman_r,
            spearman_p=spearman_p,
            bias=bias,
            mse=mse,
            mape=mape,
            n_observations=len(obs),
        )

    # ── Cobertura (calculada separadamente pois depende do total do GS) ────────

    @staticmethod
    def calculate_coverage(matched_count: int, gs_total: int) -> float:
        """
        % de metabolitos do GS identificados pela ferramenta neste espectro.
        Args:
            matched_count: nº de metabolitos presentes em ambos (JOIN count)
            gs_total:      nº total de metabolitos no GS para este espectro
        Returns:
            Percentual entre 0.0 e 100.0
        """
        if gs_total == 0:
            return 0.0
        return round((matched_count / gs_total) * 100, 4)

    @staticmethod
    def calculate_identified_gs_pct(tool_count: int, gs_total: int) -> float:
        """
        % de metabolitos identificados pela ferramenta em relação ao GS.
        """
        if gs_total == 0:
            return 0.0
        return round((tool_count / gs_total) * 100, 4)
