import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from database.db_manager import DataBaseManager

class TestDataBaseManager:
    def test_connect_supabase(self):
        db_manager = DataBaseManager()
        conn = db_manager.connect_supabase()
        assert conn is not None, "Failed to connect to the database"


if __name__ == "__main__":
    test_db_manager = TestDataBaseManager()
    test_db_manager.test_connect_supabase()
    print("All tests passed!")