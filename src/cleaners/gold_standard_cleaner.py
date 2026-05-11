import logging
import pandas as pd
from src.cleaners.factory_cleaner import Cleaner

logger = logging.getLogger(__name__)

class GoldStandardCleaner(Cleaner):
    """
    Cleaner for Gold Standard Excel files (Chenomx format).
    It extracts the actual data from the multi-header Excel structure and
    prepares it for the standard project layout.
    """

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Cleaning Gold Standard data...")
        
        # 1. Identify where the spectra names start (ending in .cnx)
        # Search in the first column for any string ending in .cnx
        cnx_mask = df.iloc[:, 0].astype(str).str.contains(r'\.cnx$', na=False)
        if not cnx_mask.any():
            logger.warning("No '.cnx' files found in the first column. Returning raw data.")
            return df
            
        data_start_idx = df[cnx_mask].index[0]
        
        # 2. Determine metabolite names
        # Usually, they are in the row directly above data or two rows above if HMDB IDs are present.
        row_above = df.iloc[data_start_idx - 1, 0]
        if pd.notnull(row_above) and 'HMDB' in str(row_above):
            # Metabolites are 2 rows above the data start
            metabolite_names = df.iloc[data_start_idx - 2].tolist()
        else:
            # Metabolites are 1 row above the data start
            metabolite_names = df.iloc[data_start_idx - 1].tolist()
        
        # 3. Extract the data starting from the identified row
        df_clean = df.iloc[data_start_idx:].copy()
        df_clean.columns = metabolite_names
        
        # 4. Standardize the Sample column
        df_clean = df_clean.rename(columns={df_clean.columns[0]: 'Sample'})
        
        # Remove '.cnx' suffix and whitespace
        df_clean['Sample'] = (
            df_clean['Sample']
            .astype(str)
            .str.replace(r'\.cnx$', '', regex=True)
            .str.strip()
        )
        
        # 5. Clean concentration values
        # Ensure all columns except 'Sample' are numeric
        for col in df_clean.columns[1:]:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)
            
        return df_clean
