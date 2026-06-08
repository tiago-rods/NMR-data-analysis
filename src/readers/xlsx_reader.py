import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader
class XLSXReader(FactoryReader):
    """Reader implementation for Excel (XLSX) files using pandas.

    Abstracting the reader here makes it straightforward to swap the
    underlying library in the future without touching any other module.
    """

    def read(self, path: str, **kwargs) -> Any:
        """Reads an Excel file into a pandas DataFrame.

        Args:
            path (str): The path to the Excel file.
            **kwargs: Additional keyword arguments forwarded to ``pd.read_excel``.

        Returns:
            pd.DataFrame: The loaded data.

        Raises:
            RuntimeError: If the file cannot be read.
        """
        try:
            return pd.read_excel(path, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error reading XLSX file at {path}: {e}")
