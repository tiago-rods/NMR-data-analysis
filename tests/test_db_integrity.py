import pytest
from database.db_manager import DataBaseManager

@pytest.fixture(scope="module")
def db_conn():
    """Provide a psycopg2 connection for tests."""
    manager = DataBaseManager()
    yield manager.conn
    manager.conn.close()

def test_experimento_counts(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT biofluido, COUNT(*) FROM experimento GROUP BY biofluido")
    data = dict(cur.fetchall())
    assert "Soro" in data and data["Soro"] > 0, "Soro count missing or zero"
    assert "Urina" in data and data["Urina"] > 0, "Urina count missing or zero"

def test_gold_standard_rows(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT fk_experimento) FROM gold_std")
    gs_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT id_experimento) FROM experimento")
    exp_count = cur.fetchone()[0]
    # Ensure no gold_std refers to unknown experiments
    cur.execute("SELECT COUNT(*) FROM gold_std WHERE fk_experimento NOT IN (SELECT id_experimento FROM experimento)")
    unknown = cur.fetchone()[0]
    assert unknown == 0, f"Gold Standard has unknown experiment IDs: {unknown}"
    # At least one gold_std entry exists
    assert gs_count > 0, "Gold Standard table is empty"

def test_analysis_tables_not_null(db_conn):
    cur = db_conn.cursor()
    tables_columns = {
        "analise_espectro": ["fk_experimento", "fk_ferramenta_teste", "pearson_r"],
        "analise_metabolito": ["fk_metabolito", "fk_ferramenta_teste", "pearson_r"],
        "analise_ferramenta": ["fk_ferramenta_teste", "fk_ferramenta_referencia", "pearson_r"],
    }
    for table, cols in tables_columns.items():
        cols_str = ", ".join(cols)
        cur.execute(f"SELECT {cols_str} FROM {table} LIMIT 10")
        rows = cur.fetchall()
        for row in rows:
            for val in row:
                assert val is not None, f"Null value found in {table}"

def test_no_duplicate_experimentos(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT espectro, COUNT(*) FROM experimento GROUP BY espectro HAVING COUNT(*) > 1")
    dup = cur.fetchall()
    assert len(dup) == 0, f"Duplicate espectro entries: {dup}"
