import os
import pandas as pd
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.xlsx_reader import XLSXReader
from src.parsers.xlsx_parser import XLSXParser

class XLSXLoader(FactoryLoader):
    """Loader implementation for Excel (XLSX) files.

    Utilizes XLSXReader to read data and XLSXParser to parse it.
    """

    def __init__(self, reader: XLSXReader = None, parser: XLSXParser = None) -> None:
        """Initializes the XLSXLoader.

        Args:
            reader (XLSXReader, optional): The reader used for Excel files. Defaults to None.
            parser (XLSXParser, optional): The parser used for Excel data. Defaults to None.
        """
        self.reader = reader or XLSXReader()
        self.parser = parser or XLSXParser()

    def load(self, path: str, **kwargs) -> Any:
        """Loads and parses data from an Excel file.

        Args:
            path (str): The path to the Excel file.
            **kwargs: Additional keyword arguments passed to the reader.

        Returns:
            Any: The parsed data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
            raise FileNotFoundError(f"File not found: {path}")
            
        raw_data = self.reader.read(path, **kwargs)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        """Saves a data object to an Excel (XLSX) file.

        Args:
            obj (Any): The data to save. Must be a DataFrame, list, or dict.
            path (str): The destination path for the Excel file.

        Raises:
            TypeError: If the object is not a supported type.
        """
        if not isinstance(obj, (list, dict, pd.DataFrame)):
            raise TypeError("Object must be a pandas DataFrame, list, or dict to save as XLSX.")
            
        df = pd.DataFrame(obj) if not isinstance(obj, pd.DataFrame) else obj
        df.to_excel(path, index=False)

    def delete(self, path: str) -> None:
        """Deletes a file if it exists.

        Args:
            path (str): The path of the file to delete.
        """
        if self.exists(path):
            os.remove(path)

    def exists(self, path: str) -> bool:
        """Checks if a file exists.

        Args:
            path (str): The file path to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.exists(path)
