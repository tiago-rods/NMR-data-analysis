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
        Busca todos os pares (concentração da ferramenta x Gold Standard)
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

    def fetch_all_experiment_counts(self) -> dict[int, dict]:
        """
        Busca em lote todos os totais de metabolitos por experimento (GS e Tools).
        Evita o problema N+1 ao fazer queries individuais.
        
        Returns:
            Dict formatado: { experiment_id: { 'gs_total': int, 'tools': { tool_id: int } } }
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
            logger.error("Erro ao buscar contagens de experimentos em lote: %s", exc)
            raise

    def fetch_all_metabolite_counts(self) -> dict:
        """
        Busca em lote todos os totais de experimentos por metabólito (GS e Tools).
        
        Returns:
            Dict formatado: { 
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

