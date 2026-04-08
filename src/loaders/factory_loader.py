from abc import ABC, abstractmethod
from typing import Any

class FactoryLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> Any:
        """"""
        pass

    @abstractmethod
    def save(self, obj: Any, path: str) -> None:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass