from abc import ABC, abstractmethod
from typing import Any, Optional
import os

class FactoryCSVFormatter(ABC):
    def __init__(self, output_dir: str = "data/processed/formatted"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    @abstractmethod
    def format(self, file_path: str) -> Optional[str]:
        """
        Abstract method to format a CSV file into the standardized form.
        Must be implemented by specific tool formatters.
        """
        pass
