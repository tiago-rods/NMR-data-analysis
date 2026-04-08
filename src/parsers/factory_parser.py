from abc import ABC, abstractmethod
from typing import Any

class FactoryParser(ABC):
    @abstractmethod
    def parse(self, raw_data: Any) -> Any:
        """
        Parses raw data into domain-specific structures.
        """
        pass
