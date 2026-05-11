import logging
import pandas as pd
from src.formatter.factory_csv_formatter import FactoryCSVFormatter

logger = logging.getLogger(__name__)

class GoldStandardFormatter(FactoryCSVFormatter):
    """
    Formatter for Gold Standard data.
    Transposes the DataFrame so it follows the project's standard:
    Rows = Metabolites, Columns = Samples.
    """

    def format(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Formatting Gold Standard data to standard layout (rows=metabolites)...")
        
        # Ensure 'Sample' is present for indexing
        if 'Sample' not in df.columns:
            logger.error("'Sample' column missing. Cannot format.")
            return df
            
        # Transpose the data: set Sample as index, then transpose
        # Result: Index = Metabolite names, Columns = Sample names
        df_transposed = df.set_index('Sample').transpose()
        
        # Standardize index name
        df_transposed.index.name = 'metabolite'
        
        return df_transposed
