import pandas as pd
from typing import Any, List, Dict
from src.parsers.factory_parser import FactoryParser

class XLSXParser(FactoryParser):
    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parses a pandas DataFrame from Excel into a standard list of dictionaries.
        """
        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("XLSXParser expects a pandas DataFrame as input.")
            
        data = raw_data.where(pd.notnull(raw_data), None)
        return data.to_dict(orient='records')
