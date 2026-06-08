from abc import ABC, abstractmethod
from typing import Any

class FactoryLoader(ABC):
    """Abstract base class defining the interface for data loaders."""

    @abstractmethod
    def load(self, path: str, **kwargs) -> Any:
        """Loads data from the specified path.

        Args:
            path (str): The file path from which to load data.
            **kwargs: Arbitrary keyword arguments specific to the loader.

        Returns:
            Any: The object containing the loaded data.
        """
        pass

    @abstractmethod
    def save(self, obj: Any, path: str) -> None:
        """Saves the object to the specified path.

        Args:
            obj (Any): The data object to be saved.
            path (str): The destination file path.
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> None:    
        """Deletes the file at the specified path.

        Args:
            path (str): The path of the file to delete.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if the file at the specified path exists.

        Args:
            path (str): The file path to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        pass