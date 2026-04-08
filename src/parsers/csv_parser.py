import pandas as pd
from typing import Any, List, Dict
from src.parsers.factory_parser import FactoryParser

class CSVParser(FactoryParser):
    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parses a pandas DataFrame into a standard list of dictionaries.
        """
        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("CSVParser expects a pandas DataFrame as input.")
        
        # Replace NaNs with None for better standard dict processing
        data = raw_data.where(pd.notnull(raw_data), None)
        return data.to_dict(orient='records')
