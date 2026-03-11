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
import sys

dic, data = ng.jcampdx.read('/Data/jdx/Soro/1_1H.jdx')

df = pd.DataFrame({
    'x':range(len(data))
    'y':data
})

df.to_csv('1_1H.csv', index=false)

