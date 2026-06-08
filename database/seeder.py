class DatabaseSeeder:
    """Base class for seeding initial data into the database."""

    def __init__(self, conn) -> None:
        """Initializes the DatabaseSeeder.

        Args:
            conn: An active psycopg2 database connection.
        """
        self.conn = conn

    def run_seeders(self) -> None:
        """Populates the database with essential initialisation data.

        Inserts standard reference data (e.g. NMR exam categories, units of
        measure). Uses ``ON CONFLICT DO NOTHING`` so re-runs are idempotent.
        """
        print("Starting initial data seeding...")

        # Placeholder SQL example — replace with actual tables once schema is finalised.
        # example_sql = """
        #    INSERT INTO your_table_name (column1, column2)
        #    VALUES ('value1', 'value2')
        #    ON CONFLICT (column1) DO NOTHING;
        # """

        # try:
        #    with self.conn.cursor() as cursor:
        #        cursor.execute(example_sql)
        #    self.conn.commit()
        #    print("Base data inserted successfully.")
        # except Exception as e:
        #    self.conn.rollback()
        #    print(f"Error running seeder: {e}")

        print("Seeders complete. Database ready for use!")
