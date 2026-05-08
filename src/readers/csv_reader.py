import pandas as pd
from typing import Any
from src.readers.factory_reader import FactoryReader
# Pode parecer redundante, visto que já utilizo pandas, porém se posteriormente decidir mudar a forma de leitura deste formato, apenas mudo neste arquivo
class CSVReader(FactoryReader):
    def read(self, path: str, **kwargs) -> Any:
        try:
            # Definimos comment='#' por padrão para ignorar metadados de arquivos científicos (ex: MagMet)
            # Mas permitimos que o usuário sobrescreva isso via kwargs se necessário.
            params = {"comment": "#"}
            params.update(kwargs)
            return pd.read_csv(path, **params)
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file at {path}: {e}")
