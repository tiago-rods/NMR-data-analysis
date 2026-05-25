import unittest
import os
from pathlib import Path

# Supabase client wrapper used in the project
from database.db_manager import DataBaseManager

class TestDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize a single DB connection for all tests
        cls.db = DataBaseManager()
        # Ensure we have a fresh connection; supabase client is cached inside manager
        cls.supabase = cls.db.supabase

    def test_experimento_counts(self):
        """Verify that the number of experiments matches the expected counts for each biofluid."""
        result = self.supabase.table("experimento").select("biofluido", "count", count="*", aggregate="count").group("biofluido").execute()
        data = {row["biofluido"]: row["count"] for row in result.data}
        # Expected counts after successful ingestion (based on previous logs)
        self.assertEqual(data.get("Soro"), 137, "Soro experiment count should be 137")
        self.assertEqual(data.get("Urina"), 180, "Urina experiment count should be 180")

    def test_gold_standard_rows(self):
        """Check that gold_std has rows for every experiment (no missing entries)."""
        # Count rows per biofluid by joining with experimento
        query = (
            self.supabase.from_("gold_std")
            .select("experimento!inner(biofluido)")
            .count("*", "total")
            .execute()
        )
        total = query.data[0]["total"]
        # Expect total = 137 (Soro) + 180 (Urina) = 317
        self.assertEqual(total, 317, "Gold Standard should have 317 rows (one per experiment)")

    def test_analysis_tables_not_null(self):
        """Ensure that key metric columns in analysis tables are not null."""
        # Check analise_ferramenta for non‑null pearson_r values
        resp = self.supabase.table("analise_ferramenta").select("pearson_r").execute()
        for row in resp.data:
            self.assertIsNotNone(row["pearson_r"], "pearson_r should not be null in analise_ferramenta")

        # Check analise_espectro for non‑null match_count
        resp2 = self.supabase.table("analise_espectro").select("match_count").execute()
        for row in resp2.data:
            self.assertIsNotNone(row["match_count"], "match_count should not be null in analise_espectro")

    def test_no_duplicate_experimentos(self):
        """Verify that the experimento table respects the unique constraint on espectro."""
        # Attempt to insert a duplicate espectro should raise an error via RPC if we try; here we just count duplicates
        dup_query = (
            self.supabase.from_("experimento")
            .select("espectro", "count", count="*", aggregate="count")
            .group("espectro")
            .having("count", "gt", 1)
            .execute()
        )
        self.assertEqual(len(dup_query.data), 0, "There should be no duplicate espectro entries")

if __name__ == "__main__":
    unittest.main()
