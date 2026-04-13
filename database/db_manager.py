import psycopg2 as pg
import os 
from dotenv import load_dotenv

load_dotenv()

class DataBaseManager:
    def __init__(self):
        self.conn = self.connect_supabase()

    def connect_supabase(self):
        try:
            self.conn = pg.connect(
                host=os.getenv("SUPABASE_HOST"),
                port=os.getenv("SUPABASE_PORT"),
                dbname=os.getenv("SUPABASE_DB_NAME"),
                user=os.getenv("SUPABASE_USER"),
                password=os.getenv("SUPABASE_PASSWORD")
            )
            return self.conn 
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None 

if __name__ == "__main__":
    db_manager = DataBaseManager()
