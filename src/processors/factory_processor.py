from abc import ABC, abstractmethod
from typing import Any

class FactoryProcessor(ABC):
    """Abstract base class defining the interface for data processors."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        """Processes data according to specific business logic.

        Args:
            *args: Positional arguments specific to the processor implementation.
            **kwargs: Keyword arguments specific to the processor implementation.

        Returns:
            Any: The processed result.
        """
        pass
