import os
import zipfile
import urllib.request
import xml.etree.ElementTree as ET

from database.seeders.factory_seeder import FactorySeeder

# Configurações
HMDB_URL = "https://hmdb.ca/system/downloads/current/hmdb_metabolites.zip"
DATA_DIR = "data"
LOCAL_ZIP = os.path.join(DATA_DIR, "hmdb_metabolites.zip")
LOCAL_XML = os.path.join(DATA_DIR, "hmdb_metabolites.xml")


class HMDBSeeder(FactorySeeder):
    """
    Faz download e parseamento do banco HMDB para popular as tabelas
    'metabolito' e 'sinonimo_metabolito'.
    Usa iterparse para processar o XML enorme sem estourar memória.
    Herda conexão e padrão de FactorySeeder.
    """

    # ── Contrato FactorySeeder ────────────────────────────────────────────────

    def seed(self) -> None:
        """Garante que o XML existe e processa os metabolitos."""
        self._ensure_data_exists()
        self._parse_and_seed()

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _ensure_data_exists(self) -> None:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        if not os.path.exists(LOCAL_XML):
            print(f"Fazendo download do HMDB em {HMDB_URL} (pode demorar)...")
            urllib.request.urlretrieve(HMDB_URL, LOCAL_ZIP)
            print("Extraindo XML...")
            with zipfile.ZipFile(LOCAL_ZIP, "r") as zip_ref:
                zip_ref.extractall(DATA_DIR)
            print("Extração concluída.")

    def _parse_and_seed(self) -> None:
        print("Parseando XML e enviando para o Supabase...")
        context = ET.iterparse(LOCAL_XML, events=("end",))
        ns = {"hmdb": "http://www.hmdb.ca"}

        count = 0
        for event, elem in context:
            if elem.tag == "{http://www.hmdb.ca}metabolite":
                accession = elem.find("hmdb:accession", ns)
                name = elem.find("hmdb:name", ns)

                if accession is not None and name is not None:
                    hmdb_id = accession.text
                    std_name = name.text

                    try:
                        self.supabase.table("metabolito").upsert(
                            {"id_hmdb": hmdb_id, "nome_padrao": std_name},
                            on_conflict="id_hmdb",
                        ).execute()

                        synonyms_node = elem.find("hmdb:synonyms", ns)
                        if synonyms_node is not None:
                            syns_to_insert = [
                                {
                                    "fk_metabolito": hmdb_id,
                                    "nome_alternativo": syn.text,
                                    "tipo_variacao": "synonym",
                                }
                                for syn in synonyms_node.findall("hmdb:synonym", ns)
                            ]

                            if syns_to_insert:
                                self.supabase.table("sinonimo_metabolito").upsert(
                                    syns_to_insert, on_conflict="id_sinonimo"
                                ).execute()

                        count += 1
                        if count % 100 == 0:
                            print(f"  Processados {count} metabolitos...")

                    except Exception as e:
                        print(f"  Erro ao inserir {hmdb_id}: {e}")

                # Libera elemento da memória
                elem.clear()

        print(f"Concluído. Total de metabolitos processados: {count}")


if __name__ == "__main__":
    seeder = HMDBSeeder()
    seeder.run()
