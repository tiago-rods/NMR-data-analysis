import os
import zipfile
import urllib.request
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Try to import supabase, fail gracefully if not installed
try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    Client = None

# Configuration
HMDB_URL = "https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip"
DATA_DIR = "data"
LOCAL_ZIP = os.path.join(DATA_DIR, "hmdb_metabolites.zip")
LOCAL_XML = os.path.join(DATA_DIR, "hmdb_metabolites.xml")

class HMDBSeeder:
    """
    Downloads and parses the HMDB database to seed the 'metabolito' and 'sinonimo_metabolito' tables.
    Uses iterparse to handle the extremely large XML file efficiently without running out of memory.
    """
    def __init__(self):
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("Warning: SUPABASE_URL and SUPABASE_KEY must be set in .env")
            self.supabase = None
        elif Client is not None:
            self.supabase: Client = create_client(url, key)
        else:
            self.supabase = None

    def _ensure_data_exists(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        if not os.path.exists(LOCAL_XML):
            print(f"Downloading HMDB data from {HMDB_URL} (this may take a while)...")
            urllib.request.urlretrieve(HMDB_URL, LOCAL_ZIP)
            print("Extracting XML...")
            with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
                zip_ref.extractall(DATA_DIR)
            print("Extraction complete.")

    def run(self):
        self._ensure_data_exists()
        
        if not self.supabase:
            print("Cannot seed without Supabase connection. Exiting.")
            return

        print("Parsing XML and pushing to Supabase...")
        context = ET.iterparse(LOCAL_XML, events=("end",))
        ns = {'hmdb': 'http://www.hmdb.ca'}
        
        count = 0
        for event, elem in context:
            # We look for the main <metabolite> tag
            if elem.tag == '{http://www.hmdb.ca}metabolite':
                accession = elem.find('hmdb:accession', ns)
                name = elem.find('hmdb:name', ns)
                
                if accession is not None and name is not None:
                    hmdb_id = accession.text
                    std_name = name.text
                    
                    try:
                        # Insert Main Metabolite
                        self.supabase.table('metabolito').upsert(
                            {'id_hmdb': hmdb_id, 'nome_padrao': std_name}, 
                            on_conflict='id_hmdb'
                        ).execute()
                        
                        # Process Synonyms
                        synonyms_node = elem.find('hmdb:synonyms', ns)
                        if synonyms_node is not None:
                            syns_to_insert = []
                            for syn in synonyms_node.findall('hmdb:synonym', ns):
                                syns_to_insert.append({
                                    'fk_metabolito': hmdb_id,
                                    'nome_alternativo': syn.text,
                                    'tipo_variacao': 'synonym'
                                })
                            
                            # Bulk insert synonyms
                            if syns_to_insert:
                                self.supabase.table('sinonimo_metabolito').upsert(
                                    syns_to_insert, 
                                    on_conflict='id_sinonimo' # Note: we might need a constraint here, or just insert
                                ).execute()
                                
                        count += 1
                        if count % 100 == 0:
                            print(f"Processed {count} metabolites...")
                            
                    except Exception as e:
                        print(f"Error inserting {hmdb_id}: {e}")
                
                # Clear element from memory
                elem.clear()

if __name__ == "__main__":
    seeder = HMDBSeeder()
    seeder.run()
