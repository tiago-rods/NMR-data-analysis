from typing import Any, Dict
from src.parsers.factory_parser import FactoryParser

class JDXParser(FactoryParser):
    def parse(self, raw_data: Any) -> Dict[str, Any]:
        """
        Parses the raw JDX dictionary containing 'metadata' and 'data'
        from nmrglue into a standarized dictionary.
        """
        if not isinstance(raw_data, dict) or "metadata" not in raw_data or "data" not in raw_data:
            raise TypeError("JDXParser expects a dictionary with 'metadata' and 'data' keys.")
            
        return {
            "metadata": raw_data["metadata"],
            "spectral_data": raw_data["data"]
        }
