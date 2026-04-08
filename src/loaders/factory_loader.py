from abc import ABC, abstractmethod
from typing import Any

class FactoryLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> Any:
        """
        Loads data from the specified path.
        """
        pass

    @abstractmethod
    def save(self, obj: Any, path: str) -> None:
        """
        Saves the object to the specified path.
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> None:    
        """
        Deletes the file at the specified path.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Checks if the file at the specified path exists.
        """
        pass