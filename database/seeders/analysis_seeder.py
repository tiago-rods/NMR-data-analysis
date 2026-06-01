"""
AnalysisSeeder — persiste resultados estatísticos nas tabelas analíticas.

Tabelas alvo da 3FN:
  analise_espectro
  analise_metabolito
  analise_ferramenta

Todos os upserts são idempotentes: rodar múltiplas vezes não duplica dados.
"""

from __future__ import annotations

import logging
from typing import Optional

from database.seeders.factory_seeder import FactorySeeder
from src.analysis.models import (
    StatResultEspectro,
    StatResultMetabolito,
    StatResultFerramenta,
)

logger = logging.getLogger(__name__)


class AnalysisSeeder(FactorySeeder):
    """
    Persiste StatResults nas três tabelas analíticas via Supabase client.
    Herda conexão e padrão de FactorySeeder.

    Design Pattern: Factory Method — implementa seed() conforme contrato ABC.
    """

    # ── Contrato FactorySeeder ────────────────────────────────────────────────

    def seed(self, results: tuple[list[StatResultEspectro], list[StatResultMetabolito], list[StatResultFerramenta]]) -> None:
        """
        Persiste as 3 listas de StatResults nas tabelas analíticas 3FN.
        """
        espectros, metabolitos, ferramentas = results

        logger.info(
            "Iniciando seed: %d Espectros, %d Metabolitos, %d Ferramentas.",
            len(espectros), len(metabolitos), len(ferramentas)
        )

        self._seed_analise_espectro(espectros)
        self._seed_analise_metabolito(metabolitos)
        self._seed_analise_ferramenta(ferramentas)

        logger.info("Seed 3FN concluído com sucesso.")

    # ── Inserções por tabela ──────────────────────────────────────────────────

    def _seed_analise_espectro(self, results: list[StatResultEspectro]) -> None:
        if not results:
            return

        records = [
            {
                "fk_experimento":           r.experiment_id,
                "fk_ferramenta_teste":      r.tool_test_id,
                "fk_ferramenta_referencia": r.tool_ref_id,
                "gs_total_metabolitos":     r.gs_total_metabolitos,
                "tool_total_metabolitos":   r.tool_total_metabolitos,
                "match_count":              r.match_count,
                "cobertura_percent":        r.coverage_pct,
                "identificados_gs_percent": r.identified_gs_pct,
                "pearson_r":                r.pearson_r,
                "pearson_p":                r.pearson_p,
                "spearman_r":               r.spearman_r,
                "spearman_p":               r.spearman_p,
                "bias":                     r.bias,
                "mse":                      r.mse,
                "mape":                     r.mape,
                "precisao":                 r.precisao,
                "recall":                   r.recall,
            }
            for r in results
        ]

        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("analise_espectro").upsert(
                    batch,
                    on_conflict="fk_experimento,fk_ferramenta_teste,fk_ferramenta_referencia"
                ).execute()
                logger.info("analise_espectro: lote %d/%d upsertado (%d registros).", i // batch_size + 1, -(-len(records) // batch_size), len(batch))
            except Exception as exc:
                logger.error("Erro ao inserir em analise_espectro: %s", exc)
                raise

    def _seed_analise_metabolito(self, results: list[StatResultMetabolito]) -> None:
        if not results:
            return

        records = [
            {
                "fk_metabolito":            r.metabolite_id,
                "fk_ferramenta_teste":      r.tool_test_id,
                "fk_ferramenta_referencia": r.tool_ref_id,
                "n_observacoes":            r.n_observations,
                "pearson_r":                r.pearson_r,
                "pearson_p":                r.pearson_p,
                "spearman_r":               r.spearman_r,
                "spearman_p":               r.spearman_p,
                "bias":                     r.bias,
                "mse":                      r.mse,
                "mape":                     r.mape,
                "precisao":                 r.precisao,
                "recall":                   r.recall,
            }
            for r in results
        ]

        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("analise_metabolito").upsert(
                    batch,
                    on_conflict="fk_metabolito,fk_ferramenta_teste,fk_ferramenta_referencia"
                ).execute()
                logger.info("analise_metabolito: lote %d/%d upsertado (%d registros).", i // batch_size + 1, -(-len(records) // batch_size), len(batch))
            except Exception as exc:
                logger.error("Erro ao inserir em analise_metabolito: %s", exc)
                raise

    def _seed_analise_ferramenta(self, results: list[StatResultFerramenta]) -> None:
        if not results:
            return

        records = [
            {
                "fk_ferramenta_teste":            r.tool_test_id,
                "fk_ferramenta_referencia":       r.tool_ref_id,
                "n_observacoes":                  r.n_observations,
                "cobertura_media_percent":        r.coverage_mean_pct,
                "identificados_gs_media_percent": r.identified_gs_mean_pct,
                "pearson_r":                      r.pearson_r,
                "pearson_p":                      r.pearson_p,
                "spearman_r":                     r.spearman_r,
                "spearman_p":                     r.spearman_p,
                "bias":                           r.bias,
                "mse":                            r.mse,
                "mape":                           r.mape,
                "precisao":                       r.precisao,
                "recall":                         r.recall,
            }
            for r in results
        ]

        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("analise_ferramenta").upsert(
                    batch,
                    on_conflict="fk_ferramenta_teste,fk_ferramenta_referencia"
                ).execute()
                logger.info("analise_ferramenta: lote %d/%d upsertado (%d registros).", i // batch_size + 1, -(-len(records) // batch_size), len(batch))
            except Exception as exc:
                logger.error("Erro ao inserir em analise_ferramenta: %s", exc)
                raise


if __name__ == "__main__":
    # Exemplo de uso isolado (para debug)
    from database.db_manager import DataBaseManager
    from src.analysis.stats_calculator import StatsCalculator
    from src.analysis.stats_engine import StatsEngine

    db = DataBaseManager()
    calculator = StatsCalculator(db)
    engine = StatsEngine()

    observations = calculator.fetch_paired_data()
    counts = calculator.fetch_all_experiment_counts()
    metabolite_counts = calculator.fetch_all_metabolite_counts()
    results = engine.calculate_all(observations, counts, metabolite_counts)

    seeder = AnalysisSeeder()
    seeder.seed(results)
    print("Seed standalone 3FN concluído.")
