import pandas as pd
from typing import Any, List, Dict
from src.parsers.factory_parser import FactoryParser

class CSVParser(FactoryParser):
    """Parser implementation for CSV data.

    Converts pandas DataFrames loaded from CSV into standard dictionary lists.
    """
    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parses a pandas DataFrame into a standard list of dictionaries.

        Args:
            raw_data (Any): The raw data to parse, expected to be a pandas DataFrame.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the rows of the DataFrame.

        Raises:
            TypeError: If raw_data is not a pandas DataFrame.
        """
        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("CSVParser expects a pandas DataFrame as input.")
        
        # Replace NaNs with None for better standard dict processing
        data = raw_data.where(pd.notnull(raw_data), None)
        return data.to_dict(orient='records')
