import os
import pandas as pd
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.csv_reader import CSVReader
from src.parsers.csv_parser import CSVParser

class CSVLoader(FactoryLoader):
    """Loader implementation for CSV files.

    Utilizes CSVReader to read data and CSVParser to parse it into a structured format.
    """

    def __init__(self, reader: CSVReader = None, parser: CSVParser = None) -> None:
        """Initializes the CSVLoader.

        Args:
            reader (CSVReader, optional): The reader used for CSV files. Defaults to None.
            parser (CSVParser, optional): The parser used for CSV data. Defaults to None.
        """
        self.reader = reader or CSVReader()
        self.parser = parser or CSVParser()

    def load(self, path: str, **kwargs) -> Any:
        """Loads and parses data from a CSV file.

        Args:
            path (str): The path to the CSV file.
            **kwargs: Additional keyword arguments passed to the reader.

        Returns:
            Any: The parsed data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        raw_data: Any = self.reader.read(path, **kwargs)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        """Saves a data object to a CSV file.

        Args:
            obj (Any): The data to save. Must be a DataFrame, list, or dict.
            path (str): The destination path for the CSV file.

        Raises:
            TypeError: If the object is not a supported type.
        """
        if not isinstance(obj, (list, dict, pd.DataFrame)):
            raise TypeError("Object must be a pandas DataFrame, list, or dict to save as CSV.")
        
        df: pd.DataFrame = pd.DataFrame(obj) if not isinstance(obj, pd.DataFrame) else obj
        df.to_csv(path, index=False)

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
