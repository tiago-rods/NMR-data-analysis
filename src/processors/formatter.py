import pandas as pd
import nmrglue as ng
import numpy as np
from typing import Any, Dict, List
from src.processors.factory_processor import FactoryProcessor

class JDXFormatter(FactoryProcessor):
    def process(self, jdx_data_list: List[Dict[str, Any]], experiment_names: List[str]) -> pd.DataFrame:
        """
        Takes a list of JDX data dictionaries (from JDXLoader/JDXParser) and their
        experiment names. Returns a Pandas DataFrame consolidated with PPM as the index column.
        """
        if len(jdx_data_list) != len(experiment_names):
            raise ValueError("The number of data items must match the number of experiment names.")
            
        if not jdx_data_list:
            return pd.DataFrame()

        # Step 1: Use the first experiment as the PPM scale reference
        first_data = jdx_data_list[0]
        ref_udic = ng.jcampdx.guess_udic(first_data["metadata"], first_data["spectral_data"])
        ref_uc = ng.fileiobase.uc_from_udic(ref_udic)
        ppm_scale = ref_uc.ppm_scale()
        
        # Step 2: Ensure PPM is sorted in ascending order (-N, ..., 0, ..., N)
        # Assuming typical NMR data returns PPM in decreasing order (e.g. 10 to -6)
        # If ppm[0] > ppm[-1], we reverse it. Otherwise, we keep it.
        reverse_required = False
        if len(ppm_scale) > 1 and ppm_scale[0] > ppm_scale[-1]:
            reverse_required = True
            ppm_scale = ppm_scale[::-1]
            
        # Step 3: Build the dataframe
        df_dict = {
            "PPM": ppm_scale
        }
        
        for data, exp_name in zip(jdx_data_list, experiment_names):
            intensities = data["spectral_data"]
            
            # If we reversed the PPM array, we MUST reverse the intensity array to match!
            if reverse_required:
                intensities = intensities[::-1]
                
            df_dict[exp_name] = intensities
            
        df = pd.DataFrame(df_dict)
        return df
