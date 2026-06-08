from abc import ABC, abstractmethod
from typing import Any

class FactoryParser(ABC):
    """Abstract base class defining the interface for data parsers."""

    @abstractmethod
    def parse(self, raw_data: Any) -> Any:
        """Parses raw data into domain-specific structures.

        Args:
            raw_data (Any): The raw data to be parsed.

        Returns:
            Any: The parsed structured data.
        """
        pass
