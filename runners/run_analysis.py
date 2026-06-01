"""
Runner de Análise Estatística — Sprint 3.

Orquestra o pipeline completo: Load → Calculate → Persist.

  1. [Load]      StatsCalculator busca pares (ferramenta vs Gold Standard) do banco.
  2. [Calculate] StatsEngine calcula métricas nos 3 níveis de granularidade.
  3. [Persist]   AnalysisSeeder faz upsert nas tabelas analíticas.

Uso:
    python runners/run_analysis.py
    python runners/run_analysis.py --tool ASICS
    python runners/run_analysis.py --tool nmRanalysis --log-level DEBUG
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Adiciona o diretório raiz do projeto ao sys.path para importações absolutas funcionarem
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db_manager import DataBaseManager
from database.seeders.analysis_seeder import AnalysisSeeder
from src.analysis.stats_calculator import StatsCalculator
from src.analysis.stats_engine import StatsEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline de análise estatística NMR (Sprint 3).\n"
            "Calcula Pearson, Spearman, Bias, MSE, MAPE e Cobertura "
            "comparando ferramentas com o Gold Standard."
        )
    )
    parser.add_argument(
        "--tool",
        type=str,
        default=None,
        help=(
            "Nome da ferramenta a analisar (ex: ASICS, nmRanalysis, MagMet). "
            "Se omitido, analisa todas as ferramentas."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log (padrão: INFO).",
    )
    return parser.parse_args()


def run(tool_name: Optional[str] = None) -> None:
    """
    Executa o pipeline completo de análise estatística.

    Args:
        tool_name: filtrar por ferramenta específica; None → todas.
    """
    # ── 1. Load (Repository) ────────────────────────────────────────────────
    logger.info("=== ETAPA 1/3: Carregando dados do banco ===")
    db = DataBaseManager()
    calculator = StatsCalculator(db)

    observations = calculator.fetch_paired_data(tool_name=tool_name)

    if not observations:
        logger.warning(
            "Nenhuma observação encontrada%s. "
            "Verifique se os dados foram ingeridos corretamente.",
            f" para ferramenta '{tool_name}'" if tool_name else "",
        )
        return

    logger.info("%d pares (tool vs GS) carregados.", len(observations))

    # ── 2. Calculate (Strategy) ─────────────────────────────────────────────
    logger.info("=== ETAPA 2/3: Calculando métricas ===")
    engine = StatsEngine()
    counts = calculator.fetch_all_experiment_counts()
    metabolite_counts = calculator.fetch_all_metabolite_counts()
    results = engine.calculate_all(observations, counts, metabolite_counts)
    logger.info(
        "Métricas calculadas com sucesso (%d espectros, %d metabólitos, %d ferramentas).",
        len(results[0]),
        len(results[1]),
        len(results[2]),
    )

    # ── 3. Persist (AnalysisSeeder) ─────────────────────────────────────────
    logger.info("=== ETAPA 3/3: Persistindo resultados ===")
    seeder = AnalysisSeeder()
    seeder.seed(results)

    logger.info("=== Pipeline concluído com sucesso. ===")


def main() -> None:
    args = parse_args()
    logging.getLogger().setLevel(args.log_level)
    run(tool_name=args.tool)


if __name__ == "__main__":
    main()
