"""
AnalysisSeeder — persiste resultados estatísticos nas tabelas analíticas.

Tabelas alvo (já existem no banco):
  analise_comparativa — PK composta: (fk_experimento, fk_ferramenta_referencia,
                                       fk_ferramenta_teste, fk_metabolito)
  metricas            — FK → analise_comparativa (mesma PK composta)
  dados_metabolitos   — FK → analise_comparativa (cobertura por metabolito)

Ordem de inserção obrigatória:
  1. analise_comparativa  (pai)
  2. metricas             (filho)
  3. dados_metabolitos    (filho)

Todos os upserts são idempotentes: rodar múltiplas vezes não duplica dados.
"""

from __future__ import annotations

import logging
from typing import Optional

from database.seeders.factory_seeder import FactorySeeder
from src.analysis.models import StatResult

logger = logging.getLogger(__name__)


class AnalysisSeeder(FactorySeeder):
    """
    Persiste StatResults nas três tabelas analíticas via Supabase client.
    Herda conexão e padrão de FactorySeeder.

    Design Pattern: Factory Method — implementa seed() conforme contrato ABC.
    """

    # ── Contrato FactorySeeder ────────────────────────────────────────────────

    def seed(self, results: list[StatResult]) -> None:
        """
        Persiste uma lista de StatResults nas tabelas analíticas.

        Apenas resultados com experiment_id preenchido alimentam
        analise_comparativa (granularidade por espectro).
        Todos os resultados alimentam metricas e dados_metabolitos.

        Args:
            results: lista de StatResult gerada pelo StatsEngine.
        """
        per_experiment = [r for r in results if r.experiment_id is not None]
        all_results = results

        logger.info(
            "Iniciando seed: %d resultados por espectro, %d no total.",
            len(per_experiment),
            len(all_results),
        )

        # 1. Pai: analise_comparativa (apenas granularidade por espectro)
        self._seed_analise_comparativa(per_experiment)

        # 2. Filhos: metricas e dados_metabolitos (todos os níveis)
        self._seed_metricas(all_results)
        self._seed_dados_metabolitos(per_experiment)

        logger.info("Seed concluído com sucesso.")

    # ── Inserções por tabela ──────────────────────────────────────────────────

    def _seed_analise_comparativa(self, results: list[StatResult]) -> None:
        """
        Upsert em analise_comparativa.
        PK: (fk_experimento, fk_ferramenta_referencia, fk_ferramenta_teste, fk_metabolito)
        """
        if not results:
            return

        records = [
            {
                "fk_experimento":           r.experiment_id,
                "fk_ferramenta_referencia": r.tool_ref_id,
                "fk_ferramenta_teste":      r.tool_test_id,
                "fk_metabolito":            r.metabolite_id,
                "metodo":                   "pearson+spearman",
            }
            for r in results
        ]

        try:
            self.supabase.table("analise_comparativa").upsert(
                records,
                on_conflict=(
                    "fk_experimento,"
                    "fk_ferramenta_referencia,"
                    "fk_ferramenta_teste,"
                    "fk_metabolito"
                ),
            ).execute()
            logger.info("analise_comparativa: %d registros upsertados.", len(records))
        except Exception as exc:
            logger.error("Erro ao inserir em analise_comparativa: %s", exc)
            raise

    def _seed_metricas(self, results: list[StatResult]) -> None:
        """
        Upsert em metricas.
        FK → analise_comparativa (apenas para resultados com experiment_id).
        Apenas resultados com experiment_id não-nulo são inseridos para respeitar
        a restrição NOT NULL de fk_experimento no banco de dados.
        """
        # Filtra resultados agregados (experiment_id=None) que violariam a constraint
        valid_results = [r for r in results if r.experiment_id is not None]
        if not valid_results:
            return

        records = [
            {
                "fk_experimento":           r.experiment_id,
                "fk_ferramenta_referencia": r.tool_ref_id,
                "fk_ferramenta_teste":      r.tool_test_id,
                "fk_metabolito_analise":    r.metabolite_id,
                "pearson_r":                r.pearson_r,
                "pearson_p":                r.pearson_p,
                "spearman_r":               r.spearman_r,
                "spearman_p":               r.spearman_p,
                "bias":                     r.bias,
                "mse":                      r.mse,
                "mape":                     r.mape,
            }
            for r in valid_results
        ]

        # Inserção em lotes para não sobrecarregar a API
        batch_size = 500

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("metricas").upsert(batch).execute()
                logger.info(
                    "metricas: lote %d/%d upsertado (%d registros).",
                    i // batch_size + 1,
                    -(-len(records) // batch_size),
                    len(batch),
                )
            except Exception as exc:
                logger.error("Erro ao inserir lote em metricas (offset=%d): %s", i, exc)
                raise

    def _seed_dados_metabolitos(self, results: list[StatResult]) -> None:
        """
        Upsert em dados_metabolitos com cobertura_percent e identificados_gs_percent.
        Apenas resultados com experiment_id (granularidade por espectro).
        FK → analise_comparativa.
        """
        if not results:
            return

        records = [
            {
                "fk_experimento":           r.experiment_id,
                "fk_ferramenta_referencia": r.tool_ref_id,
                "fk_ferramenta_teste":      r.tool_test_id,
                "fk_metabolito_analise":    r.metabolite_id,
                "cobertura_percent":        r.coverage_pct,
                "identificados_gs_percent": r.identified_gs_pct,
            }
            for r in results
        ]

        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("dados_metabolitos").upsert(batch).execute()
                logger.info(
                    "dados_metabolitos: lote %d/%d upsertado (%d registros).",
                    i // batch_size + 1,
                    -(-len(records) // batch_size),
                    len(batch),
                )
            except Exception as exc:
                logger.error(
                    "Erro ao inserir lote em dados_metabolitos (offset=%d): %s", i, exc
                )
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
    results = engine.calculate_all(observations)

    seeder = AnalysisSeeder()
    seeder.seed(results)
    print(f"Concluído: {len(results)} StatResults persistidos.")
