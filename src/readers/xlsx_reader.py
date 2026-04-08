import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader

class XLSXReader(FactoryReader):
    def read(self, path: str) -> Any:
        try:
            return pd.read_excel(path)
        except Exception as e:
            raise RuntimeError(f"Error reading XLSX file at {path}: {e}")
