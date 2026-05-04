import logging
import re
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from src.cleaners.factory_cleaner import Cleaner

class MagMetCleaner(Cleaner):
    """Cleaner for MagMet data."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Strip .fid suffix from column names
        df.columns = [str(col).replace(".fid", "").strip() for col in df.columns]

        # 2. Drop HMDB ID if exists (as per formatter)
        if "HMDB ID" in df.columns:
            df = df.drop(columns=["HMDB ID"])

        # 3. Set 'Compound Name' as index if present
        if "Compound Name" in df.columns:
            df = df.set_index("Compound Name")
            df.index.name = "metabolite"

        # 4. Standardize missing values and enforce numeric
        df = df.fillna(0).replace("", 0)
        df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

        return df

