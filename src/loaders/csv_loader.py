import os
import pandas as pd
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.csv_reader import CSVReader
from src.parsers.csv_parser import CSVParser

class CSVLoader(FactoryLoader):
    def __init__(self, reader: CSVReader = None, parser: CSVParser = None):
        self.reader = reader or CSVReader()
        self.parser = parser or CSVParser()

    def load(self, path: str, **kwargs) -> Any:
        if not self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        raw_data: Any = self.reader.read(path, **kwargs)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        if not isinstance(obj, (list, dict, pd.DataFrame)):
            raise TypeError("Object must be a pandas DataFrame, list, or dict to save as CSV.")
        
        df: pd.DataFrame = pd.DataFrame(obj) if not isinstance(obj, pd.DataFrame) else obj
        df.to_csv(path, index=False)

    def delete(self, path: str) -> None:
        if self.exists(path):
            os.remove(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)
