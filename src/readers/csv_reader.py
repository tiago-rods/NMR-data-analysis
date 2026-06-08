import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader
class CSVReader(FactoryReader):
    """Reader implementation for CSV files using pandas.

    Abstracting the reader here makes it straightforward to swap the
    underlying library in the future without touching any other module.
    """

    def read(self, path: str, **kwargs) -> Any:
        """Reads a CSV file into a pandas DataFrame.

        Sets ``comment='#'`` by default to skip metadata lines found in
        scientific file formats (e.g. MagMet). This can be overridden via
        ``**kwargs``.

        Args:
            path (str): The path to the CSV file.
            **kwargs: Additional keyword arguments forwarded to ``pd.read_csv``.

        Returns:
            pd.DataFrame: The loaded data.

        Raises:
            RuntimeError: If the file cannot be read.
        """
        try:
            params = {"comment": "#"}
            params.update(kwargs)
            return pd.read_csv(path, **params)
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file at {path}: {e}")
