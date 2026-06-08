import pandas as pd
import json
from typing import Dict

def convert_wide_to_jsonb(df: pd.DataFrame) -> Dict[str, str]:
    """Converts a wide-format DataFrame into a dictionary of JSON strings.

    Each key is a spectrum/sample name (column header) and each value is a
    JSON-encoded list of ``{"metabolite": str, "concentration": float}`` dicts
    containing only non-zero concentration entries.

    Args:
        df (pd.DataFrame): Wide-format DataFrame with ``'metabolite'`` as the
            index (or a column) and spectrum names as columns.

    Returns:
        Dict[str, str]: Mapping from spectrum name to its JSON string.
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
