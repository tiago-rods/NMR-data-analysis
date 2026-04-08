import nmrglue as ng
from typing import Any
from src.readers.factory_reader import FactoryReader

class JDXReader(FactoryReader):
    def read(self, path: str) -> Any:
        try:
            # nmrglue jcampdx.read returns (dic, data)
            dic, data = ng.jcampdx.read(path)
            return {"metadata": dic, "data": data}
        except Exception as e:
            raise RuntimeError(f"Error reading JDX file at {path}: {e}")
