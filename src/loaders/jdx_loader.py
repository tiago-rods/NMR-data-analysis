import os
from typing import Any
from src.loaders.factory_loader import FactoryLoader
from src.readers.jdx_reader import JDXReader
from src.parsers.jdx_parser import JDXParser

class JDXLoader(FactoryLoader):
    """Loader implementation for JDX (JCAMP-DX) NMR data files.

    Utilizes JDXReader for file reading and JDXParser for structural parsing.
    """

    def __init__(self, reader: JDXReader = None, parser: JDXParser = None) -> None:
        """Initializes the JDXLoader.

        Args:
            reader (JDXReader, optional): The reader used for JDX files. Defaults to None.
            parser (JDXParser, optional): The parser used for JDX data. Defaults to None.
        """
        self.reader = reader or JDXReader()
        self.parser = parser or JDXParser()

    def load(self, path: str, **kwargs) -> Any:
        """Loads and parses data from a JDX file.

        Args:
            path (str): The path to the JDX file.
            **kwargs: Additional keyword arguments passed to the reader.

        Returns:
            Any: The parsed data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        raw_data = self.reader.read(path, **kwargs)
        return self.parser.parse(raw_data)

    def save(self, obj: Any, path: str) -> None:
        """Saves a data object to a JDX file.

        Args:
            obj (Any): The data to save.
            path (str): The destination path for the JDX file.

        Raises:
            NotImplementedError: Saving to JDX is currently unsupported.
        """
        raise NotImplementedError("Saving JDX files is not supported at this time.")

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
