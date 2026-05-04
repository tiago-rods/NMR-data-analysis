import logging
from typing import Optional, Any
from pathlib import Path
import pandas as pd

from src.processors.factory_processor import FactoryProcessor
from src.readers.csv_reader import CSVReader
from src.cleaners.factory_cleaner import Cleaner
from src.formatter.factory_csv_formatter import FactoryCSVFormatter

logger = logging.getLogger(__name__)

class DataProcessor(FactoryProcessor):
    """
    Orchestrator for the NMR data pipeline.
    Connects Readers, Cleaners, and Formatters.
    """

    def __init__(
        self,
        reader: Any,
        cleaner: Optional[Cleaner] = None,
        formatter: Optional[FactoryCSVFormatter] = None
    ):
        self.reader = reader
        self.cleaner = cleaner
        self.formatter = formatter

    def process(self, file_path: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Executes the processing pipeline for a single file.
        """
        try:
            logger.info(f"Processing file: {file_path}")

            # 1. Read
            df = self.reader.read(file_path, **kwargs)

            # 2. Clean
            if self.cleaner:
                df = self.cleaner.clean(df)

            # 3. Format (Note: Current formatters handle saving, we might want to change this)
            # For now, let's just return the cleaned/formatted DataFrame
            return df

        except Exception as e:
            logger.error(f"Error in processing pipeline for {file_path}: {e}")
            return None
