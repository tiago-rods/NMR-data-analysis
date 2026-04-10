import pandas as pd
import nmrglue as ng
import numpy as np
from typing import Any, Dict, List
from src.processors.factory_processor import FactoryProcessor

class JDXFormatter(FactoryProcessor):
    def process(self, jdx_data_list: List[Dict[str, Any]], experiment_names: List[str], sample_type: str = None) -> pd.DataFrame:
        """
        Takes a list of JDX data dictionaries and experiment names.
        Automatically calibrates the PPM scale such that the reference peak (TSP) is at 0.0.
        Returns a consolidated Pandas DataFrame.
        """
        if len(jdx_data_list) != len(experiment_names):
            raise ValueError("The number of data items must match the number of experiment names.")
            
        if not jdx_data_list:
            return pd.DataFrame()

        # Define the search window for the reference peak (TSP) based on sample type
        # Based on user feedback: Soro ~ -4 PPM, Urina ~ -3 PPM
        if sample_type == "Soro":
            window = (-5.0, -2.0)
        elif sample_type == "Urina":
            window = (-4.0, -1.0)
        else:
            window = (-1.0, 1.0) # Default narrow search

        aligned_results = []
        
        # We'll use the first experiment's scale (after its own calibration) 
        # as the master grid for all others to ensure perfect alignment.
        master_ppm_grid = None

        for data, exp_name in zip(jdx_data_list, experiment_names):
            # 1. Get raw PPM scale for this file
            dic = data["metadata"]
            intensities = np.array(data["spectral_data"])
            
            udic = ng.jcampdx.guess_udic(dic, intensities)
            uc = ng.fileiobase.uc_from_udic(udic)
            raw_ppm = uc.ppm_scale()
            
            # Ensure ascending order for calibration and interpolation
            if len(raw_ppm) > 1 and raw_ppm[0] > raw_ppm[-1]:
                raw_ppm = raw_ppm[::-1]
                intensities = intensities[::-1]
            
            # 2. Find the reference peak (TSP) in the search window
            mask = (raw_ppm >= window[0]) & (raw_ppm <= window[1])
            if np.any(mask):
                sub_ppm = raw_ppm[mask]
                sub_data = intensities[mask]
                peak_ppm = sub_ppm[np.argmax(sub_data)]
                # The shift needed to move peak_ppm to 0.0
                offset = peak_ppm 
            else:
                offset = 0.0
            
            # 3. Apply the shift to the scale
            corrected_ppm = raw_ppm - offset
            
            # 4. Handle consolidation
            if master_ppm_grid is None:
                # The first experiment defines the target grid
                master_ppm_grid = corrected_ppm
                aligned_intensities = intensities
            else:
                # Interpolate this experiment's data onto the master grid
                # This handles cases where different files might have slightly different metadata/shifts
                aligned_intensities = np.interp(master_ppm_grid, corrected_ppm, intensities)
                
            aligned_results.append((exp_name, aligned_intensities))
            
        # Build the final DataFrame
        df_dict = {
            "PPM": master_ppm_grid
        }
        for name, values in aligned_results:
            df_dict[name] = values
            
        return pd.DataFrame(df_dict)
