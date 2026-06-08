from abc import ABC, abstractmethod
from typing import Any

class FactoryReader(ABC):
    """Abstract base class defining the interface for data readers."""

    @abstractmethod
    def read(self, path: str, **kwargs) -> Any:
        """Reads raw data from the specified path.

        Args:
            path (str): The file path from which to read data.
            **kwargs: Arbitrary keyword arguments specific to the reader implementation.

        Returns:
            Any: The raw data read from the file.
        """
        pass
