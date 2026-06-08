import logging
import pandas as pd
from src.cleaners.factory_cleaner import Cleaner

logger = logging.getLogger(__name__)


class GoldStandardCleaner(Cleaner):
    """
    Cleaner for Gold Standard Excel files (Chenomx format).
    It extracts the actual data from the multi‑header Excel structure and
    prepares it for the standard project layout.
    
    Args:
        df: DataFrame to clean.
    
    Returns:
        Cleaned DataFrame with columns 'Sample' and metabolite concentrations.
    """

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Cleaning Gold Standard data...")

        # Identify first row where first column ends with '.cnx'
        data_start_idx = -1
        for i, val in enumerate(df.iloc[:, 0]):
            if isinstance(val, str) and val.strip().endswith('.cnx'):
                data_start_idx = i
                break

        if data_start_idx == -1:
            # No data rows found; return original dataframe
            logger.warning("No '.cnx' files found in the first column. Returning original DataFrame.")
            return df

        # Extract data starting from identified row
        df_clean = df.iloc[data_start_idx:].copy()

        # Determine metabolite column names
        if data_start_idx == 0:
            # Data starts at first row; column names are already present
            metabolite_names = list(df.columns)
        else:
            # Check if the row above contains HMDB identifier to decide offset
            row_above = df.iloc[data_start_idx - 1, 0]
            if pd.notnull(row_above) and 'HMDB' in str(row_above):
                metabolite_names = df.iloc[data_start_idx - 2].tolist()
            else:
                metabolite_names = df.iloc[data_start_idx - 1].tolist()
            metabolite_names = [str(name).strip() for name in metabolite_names]

        # Apply column names
        df_clean.columns = metabolite_names

        # Standardize Sample column
        df_clean = df_clean.rename(columns={df_clean.columns[0]: 'Sample'})
        df_clean['Sample'] = (
            df_clean['Sample']
            .astype(str)
            .str.strip()
            .str.replace(r'\.cnx$', '', regex=True)
        )

        # Ensure numeric concentration columns
        for col in df_clean.columns[1:]:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

        return df_clean
