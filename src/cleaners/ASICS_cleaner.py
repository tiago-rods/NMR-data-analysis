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
        # 1. Normalize: if 'Experiment' or 'Metabolite' is the index, move to columns
        # This handles cases where index_col=0 was passed to read_csv
        if df.index.name in ['Experiment', 'Metabolite']:
            df = df.reset_index()

        # 2. Detect format: Long (Tidy) vs Wide
        if 'Experiment' in df.columns and 'Metabolite' in df.columns:
            logger.info("Detected ASICS Long format. Cleaning columns...")
            df['Experiment'] = df['Experiment'].astype(str).str.replace('"', '').str.strip()
            df['Metabolite'] = df['Metabolite'].astype(str).str.replace('"', '').str.strip()
            
            # Handle decimal commas if present
            if df['Concentration_uM_Final'].dtype == object:
                df['Concentration_uM_Final'] = (
                    df['Concentration_uM_Final']
                    .str.replace(',', '.')
                    .astype(float)
                )
        else:
            logger.info("Detected ASICS Wide format. Cleaning index/columns...")
            # 1. Clean experiment names (columns) and metabolite names (index)
            df.columns = [str(col).replace('"', '').strip() for col in df.columns]
            df.index = [str(idx).replace('"', '').strip() for idx in df.index]
            df.index.name = "metabolite"

        return df
    