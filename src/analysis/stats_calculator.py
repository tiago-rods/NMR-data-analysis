"""
StatsCalculator — Repository Pattern.

Unique responsibility: encapsulate all logic for accessing the database.
No other layer should execute SQL directly.

Returns PairedObservation objects ready for consumption by StatsEngine,
without exposing psycopg2 or SQL schema details to the rest of the system.
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

_ALL_GS_COUNT_QUERY = """
    SELECT fk_experimento AS experiment_id, COUNT(*) AS total
    FROM gold_std
    GROUP BY fk_experimento;
"""

_ALL_TOOL_COUNT_QUERY = """
    SELECT p.fk_experimento AS experiment_id, p.fk_ferramenta AS tool_id, COUNT(r.fk_metabolito) AS total
    FROM resultado r
    JOIN processamento p ON r.fk_processamento = p.id_processamento
    GROUP BY p.fk_experimento, p.fk_ferramenta;
"""

_ALL_GS_COUNT_BY_METABOLITE_QUERY = """
    SELECT fk_metabolito AS metabolite_id, COUNT(fk_experimento) AS total
    FROM gold_std
    GROUP BY fk_metabolito;
"""

_ALL_TOOL_COUNT_BY_METABOLITE_QUERY = """
    SELECT p.fk_ferramenta AS tool_id, r.fk_metabolito AS metabolite_id, COUNT(p.fk_experimento) AS total
    FROM resultado r
    JOIN processamento p ON r.fk_processamento = p.id_processamento
    GROUP BY p.fk_ferramenta, r.fk_metabolito;
"""



# ── Repository ────────────────────────────────────────────────────────────────

class StatsCalculator:
    """
    Repository: encapsulates all logic for accessing the database.

    Public methods:
        fetch_paired_data(tool_name)       → List[PairedObservation]
        fetch_gs_metabolite_count(exp_id)  → int
        fetch_tool_metabolite_count(...)   → int
    """

    def __init__(self, db_manager: DataBaseManager):
        self._conn = db_manager.conn
        if self._conn is None:
            raise RuntimeError(
                "DataBaseManager does not have an active connection. "
                "Check the environment variables."
            )

    # ── API pública ───────────────────────────────────────────────────────────

    def fetch_paired_data(
        self,
        tool_name: Optional[str] = None,
    ) -> list[PairedObservation]:
        """
        Fetches all pairs (tool concentration vs Gold Standard)
        via INNER JOIN. Only metabolites present in both sources are
        returned—this is intentional and correct for statistical calculation.

        Args:
            tool_name: filter by tool name (optional).
                       If None, returns pairs from all tools.

        Returns:
            List of PairedObservation ordered by tool, spectrum, and metabolite.
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
            logger.error("Error fetching paired data: %s", exc)
            raise

    def fetch_gs_metabolite_count(self, experiment_id: int) -> int:
        """
        Returns the total number of metabolites present in the Gold Standard
        for a given spectrum. Used as the denominator for % Coverage.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(_GS_METABOLITE_COUNT_QUERY, (experiment_id,))
                result = cur.fetchone()
            return int(result[0]) if result else 0
        except Exception as exc:
            logger.error(
                "Error counting GS metabolites (exp=%s): %s", experiment_id, exc
            )
            raise

    def fetch_tool_metabolite_count(
        self, tool_id: int, experiment_id: int
    ) -> int:
        """
        Returns the total number of metabolites identified by the tool
        for a given spectrum. Used to calculate identificados_gs_percent.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(_TOOL_METABOLITE_COUNT_QUERY, (tool_id, experiment_id))
                result = cur.fetchone()
            return int(result[0]) if result else 0
        except Exception as exc:
            logger.error(
                "Error counting tool metabolites (tool=%s, exp=%s): %s",
                tool_id,
                experiment_id,
                exc,
            )
            raise

    def fetch_all_experiment_counts(self) -> dict[int, dict]:
        """
        Fetches all metabolite totals by experiment (GS and Tools) in batch mode.
        Avoids the N+1 problem by using bulk queries instead of individual ones.
        
        Returns:
            Formatted dict: { experiment_id: { 'gs_total': int, 'tools': { tool_id: int } } }
        """
        counts = {}
        try:
            with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. GS Counts
                cur.execute(_ALL_GS_COUNT_QUERY)
                for row in cur.fetchall():
                    exp_id = row['experiment_id']
                    counts[exp_id] = {'gs_total': row['total'], 'tools': {}}
                
                # 2. Tool Counts
                cur.execute(_ALL_TOOL_COUNT_QUERY)
                for row in cur.fetchall():
                    exp_id = row['experiment_id']
                    tool_id = row['tool_id']
                    if exp_id not in counts:
                        counts[exp_id] = {'gs_total': 0, 'tools': {}}
                    counts[exp_id]['tools'][tool_id] = row['total']
            
            logger.info("fetch_all_experiment_counts: %d experimentos carregados.", len(counts))
            return counts
        except Exception as exc:
            logger.error("Error fetching experiment counts in batch: %s", exc)
            raise

    def fetch_all_metabolite_counts(self) -> dict:
        """
        Fetches all experiment totals by metabolite (GS and Tools) in batch mode.
        
        Returns:
            Formatted dict: { 
                'gs': { metabolite_id: int }, 
                'tools': { tool_id: { metabolite_id: int } } 
            }
        """
        counts = {'gs': {}, 'tools': {}}
        try:
            with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. GS Counts
                cur.execute(_ALL_GS_COUNT_BY_METABOLITE_QUERY)
                for row in cur.fetchall():
                    counts['gs'][row['metabolite_id'].strip()] = row['total']
                
                # 2. Tool Counts
                cur.execute(_ALL_TOOL_COUNT_BY_METABOLITE_QUERY)
                for row in cur.fetchall():
                    tool_id = row['tool_id']
                    metabolite_id = row['metabolite_id'].strip()
                    if tool_id not in counts['tools']:
                        counts['tools'][tool_id] = {}
                    counts['tools'][tool_id][metabolite_id] = row['total']
            
            logger.info("fetch_all_metabolite_counts: contagens globais de metabólitos carregadas.")
            return counts
        except Exception as exc:
            logger.error("Erro ao buscar contagens de metabólitos em lote: %s", exc)
            raise

