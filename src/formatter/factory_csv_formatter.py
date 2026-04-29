import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.readers.csv_reader import CSVReader

logger = logging.getLogger(__name__)


class FactoryCSVFormatter(ABC):
    """Abstract base class for NMR tool CSV formatters.

    Each subclass must implement the `format` method to convert a
    tool-specific CSV into the project's standardized schema.
    """

    def __init__(self, output_dir: str = "data/processed/formatted") -> None:
        self.output_dir: Path = Path(output_dir)
        self.reader: CSVReader = CSVReader()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def format(self, file_path: str) -> Optional[str]:
        """Formats a CSV file into the project's standardized schema.

        Args:
            file_path: Path to the CSV file to be formatted.

        Returns:
            Path to the generated output file, or None on failure.
        """
