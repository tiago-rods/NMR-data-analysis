import os
import pandas as pd
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.xlsx_reader import XLSXReader
from src.parsers.xlsx_parser import XLSXParser

class XLSXLoader(FactoryLoader):
    def __init__(self, reader: XLSXReader = None, parser: XLSXParser = None):
        self.reader = reader or XLSXReader()
        self.parser = parser or XLSXParser()

    def load(self, path: str) -> Any:
        if not self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        raw_data = self.reader.read(path)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        if not isinstance(obj, (list, dict, pd.DataFrame)):
            raise TypeError("Object must be a pandas DataFrame, list, or dict to save as XLSX.")
            
        df = pd.DataFrame(obj) if not isinstance(obj, pd.DataFrame) else obj
        df.to_excel(path, index=False)

    def delete(self, path: str) -> None:
        if self.exists(path):
            os.remove(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)
