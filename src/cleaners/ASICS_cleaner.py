import logging
import re
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from src.cleaners.factory_cleaner import Cleaner

logger = logging.getLogger(__name__)

class ASICSCleaner(Cleaner):
    """Cleaner for ASICS data."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Clean experiment names (columns) and metabolite names (index)
        df.columns = [str(col).replace('"', '').strip() for col in df.columns]
        df.index = [str(idx).replace('"', '').strip() for idx in df.index]
        df.index.name = "metabolite"

        return df
    