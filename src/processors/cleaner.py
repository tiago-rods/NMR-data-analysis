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

class ASICSCleaner(Cleaner):
    """Cleaner for ASICS data."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Clean experiment names (columns) and metabolite names (index)
        df.columns = [str(col).replace('"', '').strip() for col in df.columns]
        df.index = [str(idx).replace('"', '').strip() for idx in df.index]
        df.index.name = "metabolite"

        return df
