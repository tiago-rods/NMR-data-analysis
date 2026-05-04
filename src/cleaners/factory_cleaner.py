import logging
from abc import ABC, abstractmethod
import pandas as pd

logger = logging.getLogger(__name__)

class Cleaner(ABC):
    """Base class for data cleaning and standardization."""

    @abstractmethod
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies cleaning logic to the input DataFrame."""
        pass

