from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

try:
    response = supabase.table("Equipamento").select("*").execute()
    print(response.data)
except Exception as e:
    print(f"Error fetching data from Supabase: {e}")