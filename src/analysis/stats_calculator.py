"""
StatsCalculator — Repository Pattern.

Responsabilidade única: encapsular toda lógica de acesso ao banco de dados.
Nenhuma outra camada deve executar SQL diretamente.

Retorna objetos PairedObservation prontos para consumo pelo StatsEngine,
sem expor detalhes de psycopg2 ou do schema SQL para o resto do sistema.
"""

from __future__ import annotations

import logging
from typing import Optional

import psycopg2
import psycopg2.extras

from database.db_manager import DataBaseManager
from src.analysis.models import PairedObservation

logger = logging.getLogger(__name__)


# ── SQL ───────────────────────────────────────────────────────────────────────

_PAIRED_DATA_QUERY = """
    SELECT
        p.fk_ferramenta                     AS tool_test_id,
        gs_tool.id_ferramenta               AS tool_ref_id,
        p.fk_experimento                    AS experiment_id,
        r.fk_metabolito                     AS metabolite_id,
        COALESCE(e.biofluido, 'Desconhecido') AS biofluid,
        r.concentracao                      AS concentration_tool,
        g.concentracao_gs                   AS concentration_gs
    FROM resultado r
    JOIN processamento p
        ON r.fk_processamento = p.id_processamento
    JOIN gold_std g
        ON g.fk_experimento = p.fk_experimento
       AND g.fk_metabolito  = r.fk_metabolito
    JOIN experimento e
        ON e.id_experimento  = p.fk_experimento
    -- Identifica a ferramenta de referência pelo nome 'LNBioGS'
    JOIN ferramenta gs_tool
        ON gs_tool.nome = 'LNBioGS'
    {where_clause}
    ORDER BY p.fk_ferramenta, p.fk_experimento, r.fk_metabolito;
"""

_GS_METABOLITE_COUNT_QUERY = """
    SELECT COUNT(*) AS total
    FROM gold_std
    WHERE fk_experimento = %s;
"""

_TOOL_METABOLITE_COUNT_QUERY = """
    SELECT COUNT(*) AS total
    FROM resultado r
    JOIN processamento p ON r.fk_processamento = p.id_processamento
    WHERE p.fk_ferramenta  = %s
      AND p.fk_experimento = %s;
"""


# ── Repository ────────────────────────────────────────────────────────────────

class StatsCalculator:
    """
    Repository: encapsula toda lógica SQL de acesso ao banco.

    Métodos públicos:
        fetch_paired_data(tool_name)       → List[PairedObservation]
        fetch_gs_metabolite_count(exp_id)  → int
        fetch_tool_metabolite_count(...)   → int
    """

    def __init__(self, db_manager: DataBaseManager):
        self._conn = db_manager.conn
        if self._conn is None:
            raise RuntimeError(
                "DataBaseManager não possui conexão ativa. "
                "Verifique as variáveis de ambiente."
            )

    # ── API pública ───────────────────────────────────────────────────────────

    def fetch_paired_data(
        self,
        tool_name: Optional[str] = None,
    ) -> list[PairedObservation]:
        """
        Busca todos os pares (concentração da ferramenta × Gold Standard)
        via INNER JOIN. Apenas metabolitos presentes em ambas as fontes são
        retornados — isso é intencional e correto para o cálculo estatístico.

        Args:
            tool_name: filtrar por nome de ferramenta (opcional).
                       Se None, retorna pares de todas as ferramentas.

        Returns:
            Lista de PairedObservation ordenada por ferramenta, espectro e metabolito.
        """
        where_clause = ""
        params: tuple = ()

        if tool_name:
            where_clause = "JOIN ferramenta f ON f.id_ferramenta = p.fk_ferramenta WHERE f.nome = %s"
            params = (tool_name,)

        query = _PAIRED_DATA_QUERY.format(where_clause=where_clause)

        try:
            with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

            observations = [
                PairedObservation(
                    tool_test_id=row["tool_test_id"],
                    tool_ref_id=row["tool_ref_id"],
                    experiment_id=row["experiment_id"],
                    metabolite_id=row["metabolite_id"].strip(),
                    biofluid=row["biofluid"],
                    concentration_tool=float(row["concentration_tool"]),
                    concentration_gs=float(row["concentration_gs"]),
                )
                for row in rows
            ]

            logger.info(
                "fetch_paired_data: %d observações carregadas (ferramenta='%s').",
                len(observations),
                tool_name or "todas",
            )
            return observations

        except Exception as exc:
            logger.error("Erro ao buscar dados pareados: %s", exc)
            raise

    def fetch_gs_metabolite_count(self, experiment_id: int) -> int:
        """
        Retorna o total de metabolitos presentes no Gold Standard
        para um dado espectro. Usado como denominador da % de Cobertura.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(_GS_METABOLITE_COUNT_QUERY, (experiment_id,))
                result = cur.fetchone()
            return int(result[0]) if result else 0
        except Exception as exc:
            logger.error(
                "Erro ao contar metabolitos do GS (exp=%s): %s", experiment_id, exc
            )
            raise

    def fetch_tool_metabolite_count(
        self, tool_id: int, experiment_id: int
    ) -> int:
        """
        Retorna o total de metabolitos identificados pela ferramenta
        para um dado espectro. Usado para calcular identificados_gs_percent.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(_TOOL_METABOLITE_COUNT_QUERY, (tool_id, experiment_id))
                result = cur.fetchone()
            return int(result[0]) if result else 0
        except Exception as exc:
            logger.error(
                "Erro ao contar metabolitos da ferramenta (tool=%s, exp=%s): %s",
                tool_id,
                experiment_id,
                exc,
            )
            raise
