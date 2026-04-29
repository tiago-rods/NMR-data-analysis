import os
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.jdx_reader import JDXReader
from src.parsers.jdx_parser import JDXParser

class JDXLoader(FactoryLoader):
    def __init__(self, reader: JDXReader = None, parser: JDXParser = None):
        self.reader = reader or JDXReader()
        self.parser = parser or JDXParser()

    def load(self, path: str, **kwargs) -> Any:
        if not self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        raw_data = self.reader.read(path, **kwargs)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        raise NotImplementedError("Saving JDX files is not supported at this time.")

    def delete(self, path: str) -> None:
        if self.exists(path):
            os.remove(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)
