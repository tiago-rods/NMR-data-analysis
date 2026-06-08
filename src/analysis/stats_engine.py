"""
StatsEngine — Strategy Pattern.

Unique responsibility: calculate statistical metrics from
PairedObservations. No database access here.

Structure:
  MetricStrategy (ABC)       ← interface of each metric
    ├── PearsonStrategy
    ├── SpearmanStrategy
    ├── BiasStrategy
    ├── MSEStrategy
    └── MAPEStrategy

  StatsEngine                ← orchestrates the calculation across the 3 levels of granularity
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import groupby
from typing import Optional

import numpy as np
import scipy.stats

from src.analysis.models import (
    PairedObservation,
    StatResultEspectro,
    StatResultMetabolito,
    StatResultFerramenta,
)

logger = logging.getLogger(__name__)

# Minimum number of pairs required to calculate correlation metrics.
# With fewer pairs, the coefficients do not have statistical significance.
_MIN_PAIRS = 3


# ── Strategies ────────────────────────────────────────────────────────────────

class MetricStrategy(ABC):
    """Strategy interface: each subclass implements a specific metric."""

    @abstractmethod
    def calculate(
        self, tool: np.ndarray, gs: np.ndarray
    ) -> float | tuple[float, float]:
        """
        Calculates the metric between the tool and gs vectors.

        Returns:
            Unique float or (coefficient, p-value) depending on the metric.
        """
        ...


class PearsonStrategy(MetricStrategy):
    """Pearson Correlation — measures linear association."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> tuple[float, float]:
        if len(tool) < _MIN_PAIRS:
            return 0.0, 1.0
        r, p = scipy.stats.pearsonr(tool, gs)
        return float(r), float(p)


class SpearmanStrategy(MetricStrategy):
    """Spearman Correlation — measures monotonic association (robust to outliers)."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> tuple[float, float]:
        if len(tool) < _MIN_PAIRS:
            return 0.0, 1.0
        r, p = scipy.stats.spearmanr(tool, gs)
        return float(r), float(p)


class BiasStrategy(MetricStrategy):
    """Mean bias: mean(tool - gs). Positive → overestimation; negative → underestimation."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        return float(np.mean(tool - gs))


class MSEStrategy(MetricStrategy):
    """Mean Squared Error — penalizes large errors."""

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        return float(np.mean((tool - gs) ** 2))


class MAPEStrategy(MetricStrategy):
    """
    Mean Absolute Percentage Error.
    Ignores pairs where gs == 0 to avoid division by zero.
    """

    def calculate(self, tool: np.ndarray, gs: np.ndarray) -> float:
        mask = gs != 0
        if not np.any(mask):
            return 0.0
        return float(np.mean(np.abs((tool[mask] - gs[mask]) / gs[mask])) * 100)


# ── Engine ─────────────────────────────────────────────────────────────────────

class StatsEngine:
    """
    Orchestrates the calculation of metrics across the 3 levels of granularity of the 3NF:
    
    1. `analise_espectro`: Groups by (tool, spectrum) and evaluates the entire metabolic profile.
    2. `analise_metabolito`: Groups by (tool, metabolite) and evaluates one metabolite across all spectra.
    3. `analise_ferramenta`: Groups by (tool) and evaluates globally.

    Design Pattern: Strategy.
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
        self,
        observations: list[PairedObservation],
        experiment_counts: dict[int, dict],
        metabolite_counts: dict = None
    ) -> tuple[list[StatResultEspectro], list[StatResultMetabolito], list[StatResultFerramenta]]:
        """
        Calculates metrics across the 3 levels and returns the complete lists.
        `experiment_counts` must be:
        { exp_id: { 'gs_total': int, 'tools': { tool_id: int } } }
        `metabolite_counts` must be the dict returned by fetch_all_metabolite_counts.
        """
        if metabolite_counts is None:
            metabolite_counts = {'gs': {}, 'tools': {}}

        espectros = self._by_experiment(observations, experiment_counts)
        metabolitos = self._by_metabolite(observations, metabolite_counts)
        ferramentas = self._by_tool(observations, espectros)

        logger.info(
            "calculate_all: %d Espectro, %d Metabolito, %d Ferramenta gerados.",
            len(espectros), len(metabolitos), len(ferramentas)
        )
        return espectros, metabolitos, ferramentas

    # ── Level 1: by spectrum ──────────────────────────────────────────────────

    def _by_experiment(
        self,
        observations: list[PairedObservation],
        counts: dict[int, dict]
    ) -> list[StatResultEspectro]:
        """Groups by (tool_test_id, tool_ref_id, experiment_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id, o.experiment_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id, experiment_id = key
            obs_list = list(group)
            biofluid = obs_list[0].biofluid
            
            exp_data = counts.get(experiment_id, {})
            gs_total = exp_data.get('gs_total', 0)
            tool_total = exp_data.get('tools', {}).get(tool_test_id, 0)
            match_count = len(obs_list)
            
            cov_pct = self.calculate_coverage(match_count, gs_total)
            id_gs_pct = self.calculate_identified_gs_pct(tool_total, gs_total)
            precisao = self.calculate_precision(match_count, tool_total)
            recall = self.calculate_recall(match_count, gs_total)

            tool_arr = np.array([o.concentration_tool for o in obs_list], dtype=float)
            gs_arr   = np.array([o.concentration_gs   for o in obs_list], dtype=float)

            pearson_r,  pearson_p  = self._pearson.calculate(tool_arr, gs_arr)
            spearman_r, spearman_p = self._spearman.calculate(tool_arr, gs_arr)
            bias = BiasStrategy().calculate(tool_arr, gs_arr)
            mse  = MSEStrategy().calculate(tool_arr, gs_arr)
            mape = MAPEStrategy().calculate(tool_arr, gs_arr)

            results.append(StatResultEspectro(
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                experiment_id=experiment_id,
                biofluid=biofluid,
                gs_total_metabolitos=gs_total,
                tool_total_metabolitos=tool_total,
                match_count=match_count,
                coverage_pct=cov_pct,
                identified_gs_pct=id_gs_pct,
                pearson_r=pearson_r,
                pearson_p=pearson_p,
                spearman_r=spearman_r,
                spearman_p=spearman_p,
                bias=bias,
                mse=mse,
                mape=mape,
                precisao=precisao,
                recall=recall,
            ))

        return results

    # ── Level 2: by metabolite ────────────────────────────────────────────────

    def _by_metabolite(
        self, observations: list[PairedObservation], counts: dict
    ) -> list[StatResultMetabolito]:
        """Groups by (tool_test_id, tool_ref_id, metabolite_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id, o.metabolite_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id, metabolite_id = key
            obs_list = list(group)

            gs_total = counts['gs'].get(metabolite_id, 0)
            tool_total = counts['tools'].get(tool_test_id, {}).get(metabolite_id, 0)
            match_count = len(obs_list)

            precisao = self.calculate_precision(match_count, tool_total)
            recall = self.calculate_recall(match_count, gs_total)

            tool_arr = np.array([o.concentration_tool for o in obs_list], dtype=float)
            gs_arr   = np.array([o.concentration_gs   for o in obs_list], dtype=float)

            pearson_r,  pearson_p  = self._pearson.calculate(tool_arr, gs_arr)
            spearman_r, spearman_p = self._spearman.calculate(tool_arr, gs_arr)
            bias = BiasStrategy().calculate(tool_arr, gs_arr)
            mse  = MSEStrategy().calculate(tool_arr, gs_arr)
            mape = MAPEStrategy().calculate(tool_arr, gs_arr)

            results.append(StatResultMetabolito(
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                metabolite_id=metabolite_id,
                n_observations=match_count,
                pearson_r=pearson_r,
                pearson_p=pearson_p,
                spearman_r=spearman_r,
                spearman_p=spearman_p,
                bias=bias,
                mse=mse,
                mape=mape,
                precisao=precisao,
                recall=recall,
            ))

        return results

    # ── Level 3: by tool (total) ───────────────────────────────────────

    def _by_tool(
        self,
        observations: list[PairedObservation],
        espectros: list[StatResultEspectro]
    ) -> list[StatResultFerramenta]:
        """Groups by (tool_test_id, tool_ref_id)."""
        results = []
        key_fn = lambda o: (o.tool_test_id, o.tool_ref_id)

        for key, group in groupby(sorted(observations, key=key_fn), key=key_fn):
            tool_test_id, tool_ref_id = key
            obs_list = list(group)
            
            tool_arr = np.array([o.concentration_tool for o in obs_list], dtype=float)
            gs_arr   = np.array([o.concentration_gs   for o in obs_list], dtype=float)

            pearson_r,  pearson_p  = self._pearson.calculate(tool_arr, gs_arr)
            spearman_r, spearman_p = self._spearman.calculate(tool_arr, gs_arr)
            bias = BiasStrategy().calculate(tool_arr, gs_arr)
            mse  = MSEStrategy().calculate(tool_arr, gs_arr)
            mape = MAPEStrategy().calculate(tool_arr, gs_arr)
            
            tool_espectros = [e for e in espectros if e.tool_test_id == tool_test_id]
            cov_mean = float(np.mean([e.coverage_pct for e in tool_espectros])) if tool_espectros else 0.0
            id_gs_mean = float(np.mean([e.identified_gs_pct for e in tool_espectros])) if tool_espectros else 0.0
            precisao_mean = float(np.mean([e.precisao for e in tool_espectros])) if tool_espectros else 0.0
            recall_mean = float(np.mean([e.recall for e in tool_espectros])) if tool_espectros else 0.0

            results.append(StatResultFerramenta(
                tool_test_id=tool_test_id,
                tool_ref_id=tool_ref_id,
                n_observations=len(obs_list),
                coverage_mean_pct=cov_mean,
                identified_gs_mean_pct=id_gs_mean,
                pearson_r=pearson_r,
                pearson_p=pearson_p,
                spearman_r=spearman_r,
                spearman_p=spearman_p,
                bias=bias,
                mse=mse,
                mape=mape,
                precisao=precisao_mean,
                recall=recall_mean,
            ))

        return results

    # ── Coverage (calculated separately as it depends on the GS total) ────────

    @staticmethod
    def calculate_coverage(matched_count: int, gs_total: int) -> float:
        """
        % of GS metabolites identified by the tool in this spectrum.
        Args:
            matched_count: nº of metabolites present in both (JOIN count)
            gs_total:      total nº of metabolites in GS for this spectrum
        Returns:
            Percentage between 0.0 and 100.0
        """
        if gs_total == 0:
            return 0.0
        return round((matched_count / gs_total) * 100, 4)

    @staticmethod
    def calculate_identified_gs_pct(tool_count: int, gs_total: int) -> float:
        """
        % of GS metabolites identified by the tool.
        """
        if gs_total == 0:
            return 0.0
        return round((tool_count / gs_total) * 100, 4)

    @staticmethod
    def calculate_precision(tp: int, total_tool: int) -> float:
        """
        Precisão: TP / (TP + FP)
        """
        if total_tool == 0:
            return 0.0
        return round(tp / total_tool, 4)

    @staticmethod
    def calculate_recall(tp: int, total_gs: int) -> float:
        """
        Recall: TP / (TP + FN)
        """
        if total_gs == 0:
            return 0.0
        return round(tp / total_gs, 4)
