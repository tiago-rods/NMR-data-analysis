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
    """Orchestrator for the NMR data processing pipeline.

    Connects a Reader, an optional Cleaner, and an optional Formatter
    to produce cleaned and formatted CSV outputs from raw NMR data.
    """

    def __init__(
        self,
        reader: Any,
        output_dir: str,
        cleaner: Optional[Cleaner] = None,
        formatter: Optional[FactoryCSVFormatter] = None
    ) -> None:
        """Initializes the DataProcessor.

        Args:
            reader (Any): The reader object used to load raw data.
            output_dir (str): Directory path where processed files will be saved.
            cleaner (Optional[Cleaner]): Optional cleaner to apply after reading.
            formatter (Optional[FactoryCSVFormatter]): Optional formatter to apply after cleaning.
        """
        self.reader = reader
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cleaner = cleaner
        self.formatter = formatter

    def process(self, file_path: str, **kwargs) -> Optional[str]:
        """Executes the Read → Clean → Format → Save pipeline for a single file.

        Args:
            file_path (str): Path to the raw input file.
            **kwargs: Additional keyword arguments forwarded to the reader.

        Returns:
            Optional[str]: The absolute path to the saved output file, or
            ``None`` if an error occurs during processing.
        """
        try:
            logger.info(f"Processing file: {file_path}")

            # 1. Read
            df = self.reader.read(file_path, **kwargs)

            # 2. Clean
            if self.cleaner:
                df = self.cleaner.clean(df)

            # 3. Format
            if self.formatter:
                df = self.formatter.format(df)

            # 4. Save
            output_path = self.output_dir / f"formatted_{Path(file_path).name}"
            df.to_csv(output_path)
            logger.info(f"Saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error in processing pipeline for {file_path}: {e}")
            return None
