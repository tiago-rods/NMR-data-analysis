from abc import ABC, abstractmethod
from typing import Any

class FactoryProcessor(ABC):
    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        """
        Processes data according to specific business logic.
        """
        pass
