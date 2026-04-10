from abc import ABC, abstractmethod
from typing import Any

class FactoryProcessor(ABC):
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Processes data according to specific business logic.
        """
        pass
