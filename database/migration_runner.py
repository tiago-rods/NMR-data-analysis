import os
import psycopg2

class MigrationRunner:
    def __init__(self, conn, migrations_dir="database/migrations"):
        self.conn = conn
        self.migrations_dir = migrations_dir

    def ensure_migrations_table(self):
        """Cria a tabela de controle de migrations se ela não existir."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.conn.cursor() as cursor:
            cursor.execute(create_table_query)
        self.conn.commit()
        print("Tabela 'schema_migrations' verificada/criada.")

    def get_applied_migrations(self):
        """Retorna uma lista dos nomes dos arquivos de migration que já foram aplicados."""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT version FROM schema_migrations;")
            # fetchall() retorna uma lista de tuplas: [('v001_init.sql',), ('v002...sql',)]
            applied = [row[0] for row in cursor.fetchall()]
        return applied

    def run_migrations(self):
        """Executa as migrations pendentes presentes na pasta de migrations."""
        self.ensure_migrations_table()
        applied_migrations = self.get_applied_migrations()

        # Lê os arquivos da pasta e garante a ordem correta pelo nome do arquivo
        all_files = sorted(os.listdir(self.migrations_dir))
        migration_files = [f for f in all_files if f.endswith(".sql")]

        # ==========================================
        # LÓGICA DE BASELINE INTELIGENTE
        # ==========================================
        # Como as tabelas já existem no Supabase, os comandos de ADD CONSTRAINT no dump
        # causariam erros se rodados novamente. Verificamos se uma tabela chave já existe.
        if "v001_init.sql" in migration_files and "v001_init.sql" not in applied_migrations:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'processamento');")
                db_already_exists = cursor.fetchone()[0]
                
            if db_already_exists:
                print("Detectado banco de dados pré-existente (Baseline Supabase)! Marcando 'v001_init.sql' como concluído sem regerar as constraints.")
                with self.conn.cursor() as cursor:
                    cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s);", ("v001_init.sql",))
                self.conn.commit()
                applied_migrations.append("v001_init.sql")
        # ==========================================

        pending_migrations = [f for f in migration_files if f not in applied_migrations]

        if not pending_migrations:
            print("O banco de dados já está atualizado. Nenhuma migration pendente.")
            return

        print(f"Encontradas {len(pending_migrations)} migrations pendentes. Iniciando...")

        for migration_file in pending_migrations:
            filepath = os.path.join(self.migrations_dir, migration_file)
            print(f"  Aplicando {migration_file}...")
            
            with open(filepath, "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                with self.conn.cursor() as cursor:
                    # Se o arquivo estiver vazio (apenas criado pelo usuário mas não preenchido), ignora
                    if sql_script.strip():
                        cursor.execute(sql_script)
                    # Registra a migration na tabela de controle
                    cursor.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s);", 
                        (migration_file,)
                    )
                self.conn.commit()
                print(f"  Sucesso: {migration_file} aplicada.")
            except psycopg2.Error as e:
                self.conn.rollback()
                print(f"Erro ao aplicar migration {migration_file}: {e}")
                print("Processo de migração interrompido.")
                break
