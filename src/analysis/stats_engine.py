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

from src.analysis.models import (
    PairedObservation,
    StatResultEspectro,
    StatResultMetabolito,
    StatResultFerramenta,
)

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
    Orquestra o cálculo de métricas nos 3 níveis de granularidade da 3FN:
    
    1. `analise_espectro`: Agrupa por (ferramenta, espectro) e avalia todo o perfil metabólico.
    2. `analise_metabolito`: Agrupa por (ferramenta, metabolito) e avalia um metabólito em todos os espectros.
    3. `analise_ferramenta`: Agrupa por (ferramenta) e avalia globalmente.

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
        Calcula métricas nos 3 níveis e retorna as listas completas.
        `experiment_counts` deve ser:
        { exp_id: { 'gs_total': int, 'tools': { tool_id: int } } }
        `metabolite_counts` deve ser o dict retornado por fetch_all_metabolite_counts.
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

    # ── Nível 1: por espectro ──────────────────────────────────────────────────

    def _by_experiment(
        self, observations: list[PairedObservation], counts: dict[int, dict]
    ) -> list[StatResultEspectro]:
        """Agrupa por (tool_test_id, tool_ref_id, experiment_id)."""
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

    # ── Nível 2: por metabolito ────────────────────────────────────────────────

    def _by_metabolite(
        self, observations: list[PairedObservation], counts: dict
    ) -> list[StatResultMetabolito]:
        """Agrupa por (tool_test_id, tool_ref_id, metabolite_id)."""
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

    # ── Nível 3: por ferramenta (total) ───────────────────────────────────────

    def _by_tool(
        self,
        observations: list[PairedObservation],
        espectros: list[StatResultEspectro]
    ) -> list[StatResultFerramenta]:
        """Agrupa por (tool_test_id, tool_ref_id)."""
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
