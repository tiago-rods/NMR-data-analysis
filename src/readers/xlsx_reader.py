import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader
# Pode parecer redundante, visto que já utilizo o pandas para ler xlsx, porem mantenho so por questão de organização e se for necessário mudar futuramente apenas mudo aqui
class XLSXReader(FactoryReader):
    def read(self, path: str, **kwargs) -> Any:
        try:
            return pd.read_excel(path, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error reading XLSX file at {path}: {e}")
