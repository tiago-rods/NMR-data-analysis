from abc import ABC, abstractmethod
from typing import Any

class FactoryReader(ABC):
    @abstractmethod
    def read(self, path: str) -> Any:
        """
        Reads raw data from the specified path.
        """
        pass
