import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.readers.csv_reader import CSVReader

logger = logging.getLogger(__name__)


class FactoryCSVFormatter(ABC):
    """Abstract base class for NMR tool CSV formatters.

    Each subclass must implement the `format` method to convert a
    tool-specific DataFrame into the project's standardized schema.
    """

    @abstractmethod
    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Formats a DataFrame into the project's standardized schema.

        Args:
            df: The DataFrame to be formatted.

        Returns:
            The formatted DataFrame.
        """
        pass
