#
#
# Este arquivo deve converter o formato .jdx de RMN para .csv
# Neste .csv, deve-se conter: 
# - Primeira coluna deslocamento químico em PPM em ordem crescente
# - Primeira linha Nome dos experimentos
# - Demais lacunas, devem conter a intensidade do espectro do experimento em determinado deslocamento químico
#
#

import nmrglue as ng
import pandas as pd
import os 
import numpy as np 
from pathlib import Path

def process_directory(in_dir, out_file):
    data_dict = {}
    ppm_array = None

    for file in sorted(os.listdir(in_dir)):
        if file.lower().endswith('.jdx'):
            comp_path = os.path.join(in_dir, file)
            try:
                dic, data_y = ng.jcampdx.read(comp_path)
                
                # Extract PPM scale on the first successful read
                if ppm_array is None:
                    # ng.jcampdx.read values are typically lists of strings
                    firstx = float(dic.get('FIRSTX', dic.get('firstx', [0]))[0])
                    lastx = float(dic.get('LASTX', dic.get('lastx', [0]))[0])
                    npoints = int(dic.get('NPOINTS', dic.get('npoints', [len(data_y)]))[0])
                    obs = float(dic.get('.OBSERVEFREQUENCY', [1.0])[0])
                    
                    ppm_array = np.linspace(firstx / obs, lastx / obs, npoints)

                data_dict[file] = data_y

            except Exception as e:
                print(f"Error reading {file}: {e}")

    if ppm_array is not None and data_dict:
        # Create DataFrame
        df = pd.DataFrame({'PPM': ppm_array})
        
        for file, data_y in data_dict.items():
            if len(data_y) == len(ppm_array):
                df[file] = data_y
            else:
                print(f"Warning: {file} has {len(data_y)} points, expected {len(ppm_array)}. Skipping.")
        
        # Sort by PPM ascending
        df = df.sort_values(by='PPM', ascending=True)
        
        # Save to CSV
        df.to_csv(out_file, index=False)
        print(f"Saved successfully to {out_file}")
    else:
        print(f"No valid JDX files found in {in_dir} or missing metadata.")

if __name__ == '__main__':
    inFileSerum = os.path.join('Data', 'jdx', 'Soro')
    inFileUrine = os.path.join('Data', 'jdx', 'Urina')
    
    outFileSerumDir = os.path.join('Data', 'csv', 'Soro')
    outFileUrineDir = os.path.join('Data', 'csv', 'Urina')
    
    Path(outFileSerumDir).mkdir(parents=True, exist_ok=True)
    Path(outFileUrineDir).mkdir(parents=True, exist_ok=True)

    outFileSerum = os.path.join(outFileSerumDir, 'LNBio_Soro.csv')
    outFileUrine = os.path.join(outFileUrineDir, 'LNBio_Urina.csv')

    print("Processando Soro...")
    if os.path.exists(inFileSerum):
        process_directory(inFileSerum, outFileSerum)
    else:
        print(f"Directory missing: {inFileSerum}")

    print("\nProcessando Urina...")
    if os.path.exists(inFileUrine):
        process_directory(inFileUrine, outFileUrine)
    else:
        print(f"Directory missing: {inFileUrine}")
