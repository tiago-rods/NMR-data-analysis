import os
import psycopg2

class MigrationRunner:
    """Applies pending SQL migration files to the database in order.

    Tracks applied migrations in a ``schema_migrations`` table so each
    file is executed exactly once. Includes a baseline-detection mechanism
    to handle pre-existing Supabase databases without re-running DDL.
    """

    def __init__(self, conn, migrations_dir: str = "database/migrations") -> None:
        """Initializes the MigrationRunner.

        Args:
            conn: An active psycopg2 database connection.
            migrations_dir (str): Path to the directory containing ``.sql`` migration files.
                Defaults to ``"database/migrations"``.
        """
        self.conn = conn
        self.migrations_dir = migrations_dir

    def ensure_migrations_table(self) -> None:
        """Creates the migration tracking table if it does not already exist."""
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
        print("Table 'schema_migrations' verified/created.")

    def get_applied_migrations(self) -> list[str]:
        """Retrieves the list of already-applied migration filenames.

        Returns:
            list[str]: Filenames of migrations recorded in ``schema_migrations``.
        """
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT version FROM schema_migrations;")
            # fetchall() returns a list of tuples: [('v001_init.sql',), ...]
            applied = [row[0] for row in cursor.fetchall()]
        return applied

    def run_migrations(self) -> None:
        """Discovers and applies all pending SQL migration files in sorted order.

        Includes a smart baseline detection step: if the database schema already
        exists (e.g. a pre-existing Supabase instance), ``v001_init.sql`` is
        marked as applied without re-executing its DDL statements, preventing
        duplicate-constraint errors.
        """
        self.ensure_migrations_table()
        applied_migrations = self.get_applied_migrations()

        # Read and sort migration files to guarantee execution order
        all_files = sorted(os.listdir(self.migrations_dir))
        migration_files = [f for f in all_files if f.endswith(".sql")]

        # ── Baseline detection ───────────────────────────────────────────────
        # Tables may already exist on Supabase; running ADD CONSTRAINT again
        # would raise errors. Check for a key table before applying v001.
        if "v001_init.sql" in migration_files and "v001_init.sql" not in applied_migrations:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'processamento');"
                )
                db_already_exists = cursor.fetchone()[0]

            if db_already_exists:
                print(
                    "Pre-existing database detected (Supabase Baseline)! "
                    "Marking 'v001_init.sql' as applied without re-running constraints."
                )
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s);",
                        ("v001_init.sql",)
                    )
                self.conn.commit()
                applied_migrations.append("v001_init.sql")
        # ────────────────────────────────────────────────────────────────────

        pending_migrations = [f for f in migration_files if f not in applied_migrations]

        if not pending_migrations:
            print("Database is already up to date. No pending migrations.")
            return

        print(f"Found {len(pending_migrations)} pending migration(s). Starting...")

        for migration_file in pending_migrations:
            filepath = os.path.join(self.migrations_dir, migration_file)
            print(f"  Applying {migration_file}...")

            with open(filepath, "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                with self.conn.cursor() as cursor:
                    # Skip empty files (created but not yet populated)
                    if sql_script.strip():
                        cursor.execute(sql_script)
                    # Record the migration in the tracking table
                    cursor.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s);",
                        (migration_file,)
                    )
                self.conn.commit()
                print(f"  Success: {migration_file} applied.")
            except psycopg2.Error as e:
                self.conn.rollback()
                print(f"Error applying migration {migration_file}: {e}")
                print("Migration process interrupted.")
                break
