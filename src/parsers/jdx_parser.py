from typing import Any, Dict
from src.parsers.factory_parser import FactoryParser

class JDXParser(FactoryParser):
    """Parser implementation for JDX data.

    Extracts and standardizes metadata and spectral data from nmrglue outputs.
    """
    def parse(self, raw_data: Any) -> Dict[str, Any]:
        """Parses the raw JDX dictionary into a standardized dictionary.

        Expects a dictionary containing 'metadata' and 'data' keys from nmrglue.

        Args:
            raw_data (Any): The raw data dictionary.

        Returns:
            Dict[str, Any]: A dictionary with 'metadata' and 'spectral_data'.

        Raises:
            TypeError: If the raw_data is not a valid dictionary with the required keys.
        """
        if not isinstance(raw_data, dict) or "metadata" not in raw_data or "data" not in raw_data:
            raise TypeError("JDXParser expects a dictionary with 'metadata' and 'data' keys.")
            
        return {
            "metadata": raw_data["metadata"],
            "spectral_data": raw_data["data"]
        }
