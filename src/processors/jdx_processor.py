import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import nmrglue as ng
import pandas as pd

from src.processors.factory_processor import FactoryProcessor

logger = logging.getLogger(__name__)

# TSP reference peak search windows per sample type (ppm)
_TSP_WINDOWS: dict[str, tuple[float, float]] = {
    "Soro": (-5.0, -2.0),
    "Urina": (-4.0, -1.0),
}
_DEFAULT_TSP_WINDOW: tuple[float, float] = (-1.0, 1.0)


class JDXProcessor(FactoryProcessor):
    def process(
        self,
        jdx_data_list: list[dict[str, Any]],
        experiment_names: list[str],
        sample_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """Processes and calibrates NMR spectra from JDX data.

        Aligns the PPM scale using the internal TSP reference peak (= 0.0 ppm)
        and consolidates all experiments into a single DataFrame.

        Args:
            jdx_data_list: List of dicts containing 'metadata' and 'spectral_data'.
            experiment_names: Experiment names, one per JDX file.
            sample_type: Sample type ('Soro', 'Urina', or None for default window).

        Returns:
            DataFrame with a 'PPM' column and one column per experiment.

        Raises:
            ValueError: If the number of data items and names do not match.
        """
        if len(jdx_data_list) != len(experiment_names):
            raise ValueError("The number of data items must match the number of experiment names.")

        if not jdx_data_list:
            return pd.DataFrame()

        # Select TSP search window via dict lookup (avoids chained if/elif)
        window: tuple[float, float] = _TSP_WINDOWS.get(sample_type, _DEFAULT_TSP_WINDOW)

        aligned_results: list[tuple[str, np.ndarray]] = []
        master_ppm_grid: Optional[np.ndarray] = None

        for data, exp_name in zip(jdx_data_list, experiment_names):
            # 1. Extract raw PPM scale
            dic: dict[str, Any] = data["metadata"]
            intensities: np.ndarray = np.array(data["spectral_data"])

            udic = ng.jcampdx.guess_udic(dic, intensities)
            uc = ng.fileiobase.uc_from_udic(udic)
            raw_ppm: np.ndarray = uc.ppm_scale()

            # Ensure ascending order for calibration and interpolation
            if len(raw_ppm) > 1 and raw_ppm[0] > raw_ppm[-1]:
                raw_ppm = raw_ppm[::-1]
                intensities = intensities[::-1]

            # 2. Locate the TSP peak within the search window
            mask: np.ndarray = (raw_ppm >= window[0]) & (raw_ppm <= window[1])
            if np.any(mask):
                sub_ppm: np.ndarray = raw_ppm[mask]
                sub_data: np.ndarray = intensities[mask]
                offset: float = float(sub_ppm[np.argmax(sub_data)])
            else:
                offset = 0.0

            # 3. Apply chemical shift correction
            corrected_ppm: np.ndarray = raw_ppm - offset

            # 4. Consolidate using the first experiment as the master grid
            if master_ppm_grid is None:
                master_ppm_grid = corrected_ppm
                aligned_intensities: np.ndarray = intensities
            else:
                aligned_intensities = np.interp(master_ppm_grid, corrected_ppm, intensities)

            aligned_results.append((exp_name, aligned_intensities))

        # Build the final DataFrame using dict unpacking
        df_dict: dict[str, np.ndarray] = {
            "PPM": master_ppm_grid,
            **{name: values for name, values in aligned_results},
        }

        return pd.DataFrame(df_dict)