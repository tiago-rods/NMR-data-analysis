import pandas as pd
import json
from typing import Dict

def convert_wide_to_jsonb(df: pd.DataFrame) -> Dict[str, str]:
    """
    Converts a standardized wide DataFrame into a dictionary where:
    - Key: Spectrum/Sample Name
    - Value: JSON string of results [{"metabolite": "...", "concentration": ...}, ...]
    
    Args:
        df: DataFrame with 'metabolite' as index and spectrum names as columns.
    
    Returns:
        Dict[spectrum_name, json_string]
    """
    # Ensure index is named metabolite
    if df.index.name != 'metabolite' and 'metabolite' in df.columns:
        df = df.set_index('metabolite')
    
    json_results = {}
    
    for spectrum_name in df.columns:
        col_str = str(spectrum_name)
        if col_str.lower() in ("sample", "id", "metabolite") or col_str.startswith("Unnamed:"):
            continue
            
        # Extract series for this spectrum
        spectrum_series = df[spectrum_name]
        
        # Filter non-zero values to save space and processing time
        non_zero = spectrum_series[spectrum_series > 0]
        
        # Build list of dicts
        results_list = [
            {"metabolite": str(m), "concentration": float(c)}
            for m, c in non_zero.items()
        ]
        
        # Convert to JSON string
        json_results[spectrum_name] = json.dumps(results_list)
        
    return json_results
