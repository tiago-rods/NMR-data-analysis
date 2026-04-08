import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader

class CSVReader(FactoryReader):
    def read(self, path: str) -> Any:
        try:
            return pd.read_csv(path)
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file at {path}: {e}")
