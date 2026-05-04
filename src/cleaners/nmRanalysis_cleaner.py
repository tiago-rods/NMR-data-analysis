import logging
import re
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from src.cleaners.factory_cleaner import Cleaner

class NmRanalysisCleaner(Cleaner):
    """Cleaner for nmRanalysis data."""

    _REQUIRED_COLS: list[str] = ["Sample", "Metabolite", "Quantity", "Fitting Error"]

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Validate required columns
        missing = [c for c in self._REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # 2. Coerce numeric types
        df["Fitting Error"] = pd.to_numeric(df["Fitting Error"], errors="coerce")
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

        # 3. Extract base metabolite name
        df["Base_Metabolite"] = df["Metabolite"].str.replace(
            r"\s+\[\d+\]$", "", regex=True
        )

        # 4. Select best fit (lowest error)
        best_idx = df.groupby(["Sample", "Base_Metabolite"])["Fitting Error"].idxmin()
        df = df.loc[best_idx].copy()

        # 5. Clean sample names (remove 'X' prefix)
        df["Sample"] = df["Sample"].astype(str).str.replace(r"^X", "", regex=True)

        return df

