import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carrega variaveis do .env
load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT"),
        database=os.getenv("SUPABASE_DB_NAME"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )

def setup_db_environment(cur):
    """Garante que todas as constraints e procedures existam no banco."""
    print(">> Preparando ambiente do banco (Constraints e Procedures)...")
    
    # 1. Aplicar Constraints
    constraints = [
        ("ferramenta", "ferramenta_nome_versao_tecnologia_key", "UNIQUE (nome, versao, tecnologia)"),
        ("instrumentos", "instrumentos_frequencia_fabricante_key", "UNIQUE (frequencia, fabricante)"),
        ("experimento", "experimento_espectro_key", "UNIQUE (espectro)"),
        ("processamento", "processamento_fk_experimento_fk_ferramenta_key", "UNIQUE (fk_experimento, fk_ferramenta)"),
        ("resultado", "resultado_fk_processamento_fk_metabolito_key", "UNIQUE (fk_processamento, fk_metabolito)"),
        ("gold_std", "gold_std_fk_experimento_fk_metabolito_key", "UNIQUE (fk_experimento, fk_metabolito)")
    ]
    for table, name, definition in constraints:
        try:
            cur.execute(f"ALTER TABLE public.{table} ADD CONSTRAINT {name} {definition};")
        except Exception:
            pass 

    # 2. Instalar Procedures
    sql_files = [
        'database/plpgsql/get_metabolite_id.sql',
        'database/plpgsql/ingest_experiment_data.sql',
        'database/plpgsql/ingest_gold_standard.sql'
    ]
    for file_path in sql_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                cur.execute(sql)
            print(f"[INFO] SQL '{file_path}' instalado.")
        except Exception as e:
            print(f"[WARN] Erro ao instalar {file_path}: {e}")

def test_full_ingestion_cycle():
    print(">> Iniciando Teste de Integracao de Banco de Dados...")
    conn = get_connection()
    conn.autocommit = True 
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Setup inicial
    setup_db_environment(cur)
    
    tool_id = None
    exp_id = None
    inst_id = None
    
    try:
        # 1. SETUP: Criar ferramenta, instrumento e experimento de teste
        print("--- Etapa 1: Setup de Dados de Teste ---")
        
        # Inserir Ferramenta
        cur.execute("""
            INSERT INTO public.ferramenta (nome, versao, tecnologia, tempo_medio_processamento) 
            VALUES ('TEST_TOOL', '1.0.0', 'csv', 10.0) 
            ON CONFLICT (nome, versao, tecnologia) DO UPDATE SET nome = EXCLUDED.nome
            RETURNING id_ferramenta;
        """)
        tool_id = cur.fetchone()['id_ferramenta']
        
        # Inserir Instrumento
        cur.execute("""
            INSERT INTO public.instrumentos (fabricante, frequencia) 
            VALUES ('TEST_FAB', 600.0) 
            ON CONFLICT (frequencia, fabricante) DO UPDATE SET fabricante = EXCLUDED.fabricante
            RETURNING id_instrumento;
        """)
        inst_id = cur.fetchone()['id_instrumento']
        
        # Inserir Experimento
        cur.execute("""
            INSERT INTO public.experimento (espectro, fk_instrumento, biofluido) 
            VALUES ('TEST_SPEC', %s, 'Urina') 
            ON CONFLICT (espectro) DO UPDATE SET biofluido = EXCLUDED.biofluido
            RETURNING id_experimento;
        """, (inst_id,))
        exp_id = cur.fetchone()['id_experimento']
        
        print(f"[OK] Setup concluido. Exp ID: {exp_id}, Tool ID: {tool_id}")

        # 2. TESTE: Ingestao de Resultados
        print("--- Etapa 2: Testando Ingestao ---")
        test_json = json.dumps([
            {"metabolite": "Alanine", "concentration": 10.5},
            {"metabolite": "Glucose", "concentration": 200.0}
        ])
        # Nota: Usamos CAST explícito para evitar erro de 'unknown' types no CALL
        cur.execute("""
            CALL public.ingest_experiment_results(
                %s::VARCHAR, %s::VARCHAR, %s::VARCHAR, %s::VARCHAR, %s::JSONB
            );
        """, ('TEST_SPEC', 'TEST_TOOL', '1.0.0', 'csv', test_json))
        print("[OK] Ingestao via Procedure concluida.")

        # 3. TESTE: Upsert (Anti-duplicacao)
        print("--- Etapa 3: Testando Upsert ---")
        updated_json = json.dumps([
            {"metabolite": "Alanine", "concentration": 99.9}
        ])
        cur.execute("""
            CALL public.ingest_experiment_results(
                %s::VARCHAR, %s::VARCHAR, %s::VARCHAR, %s::VARCHAR, %s::JSONB
            );
        """, ('TEST_SPEC', 'TEST_TOOL', '1.0.0', 'csv', updated_json))
        
        cur.execute("SELECT count(*) FROM public.processamento WHERE fk_experimento = %s", (exp_id,))
        assert cur.fetchone()['count'] == 1
        print("[OK] Upsert validado (sem duplicatas).")

    except Exception as e:
        print(f"[FAIL] ERRO NO TESTE: {e}")
        raise
    finally:
        # 5. CLEANUP
        print("--- Etapa 5: Limpeza de Dados ---")
        if exp_id:
            cur.execute("DELETE FROM public.resultado r USING public.processamento p WHERE r.fk_processamento = p.id_processamento AND p.fk_experimento = %s", (exp_id,))
            cur.execute("DELETE FROM public.processamento WHERE fk_experimento = %s", (exp_id,))
            cur.execute("DELETE FROM public.gold_std WHERE fk_experimento = %s", (exp_id,))
            cur.execute("DELETE FROM public.experimento WHERE id_experimento = %s", (exp_id,))
        if tool_id:
            cur.execute("DELETE FROM public.ferramenta WHERE id_ferramenta = %s", (tool_id,))
        if inst_id:
            cur.execute("DELETE FROM public.instrumentos WHERE id_instrumento = %s", (inst_id,))
        print(">> Banco de dados limpo.")
        cur.close()
        conn.close()
        print(">> Teste de Integracao Concluido com Sucesso!")

if __name__ == "__main__":
    test_full_ingestion_cycle()
