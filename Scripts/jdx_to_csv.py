from typing import Any, Dict, List
import os
import sys
import pandas as pd

# Adiciona o diretório base (raiz do projeto) ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loaders.jdx_loader import JDXLoader
from src.loaders.csv_loader import CSVLoader
from src.processors.jdx_processor import JDXProcessor

def main():
    # Caminhos para as pastas de dados
    base_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    jdx_folder: str = os.path.join(base_dir, "data", "raw", "jdx", "Soro") # -> mude a pasta de aquisição de espectros aqui
    output_folder: str = os.path.join(base_dir, "outputs", "csv_tables") # -> muda a pasta de saída aqui
    output_file: str = os.path.join(output_folder, "LNBio04_Agilent_500MHz_Soro_size137.csv") # -> mude nome da saída aqui

    # Verifica se a pasta existe
    if not os.path.exists(jdx_folder):
        print(f"Erro: Pasta {jdx_folder} não encontrada.")
        return

    # Garante que a pasta de outputs exista
    os.makedirs(output_folder, exist_ok=True)

    # Coleta todos os arquivos jdx
    jdx_files: List[str] = [f for f in os.listdir(jdx_folder) if f.lower().endswith(".jdx")]
    
    if not jdx_files:
        print(f"Nenhum arquivo JDX encontrado em {jdx_folder}.")
        return

    print(f"Encontrados {len(jdx_files)} arquivos. Iniciando carregamento...")

    loader: JDXLoader = JDXLoader()
    formatter: JDXProcessor = JDXProcessor()
    csv_saver: CSVLoader = CSVLoader()

    jdx_data_list: List[Dict[str, Any]] = []
    experiment_names: List[str] = []

    # Carrega os dados individualmente
    for file_name in jdx_files:
        file_path: str = os.path.join(jdx_folder, file_name)
        try:
            print(f"Carregando: {file_name}")
            data: Dict[str, Any] = loader.load(file_path)
            
            # Remove a extensão para compor o nome do experimento (ex: '1_1H')
            exp_name: str = os.path.splitext(file_name)[0]
            
            jdx_data_list.append(data)
            experiment_names.append(exp_name)
        except Exception as e:
            print(f"Erro ao carregar {file_name}: {e}")

    if not jdx_data_list:
        print("Nenhum dado a ser carregado.")
        return

    # Detector automático de tipo de amostra para calibração
    sample_type = None
    if "Soro" in jdx_folder:
        sample_type = "Soro"
    elif "Urina" in jdx_folder:
        sample_type = "Urina"

    if sample_type:
        print(f"Tipo de amostra detectado: {sample_type}. Aplicando calibração automática de TSP...")

    # Formata a tabela com calibração
    try:
        final_df: pd.DataFrame = formatter.process(jdx_data_list, experiment_names, sample_type=sample_type)
    except Exception as e:
        print(f"Erro ao processar dados: {e}")
        return

    # Salva o arquivo CSV
    try:
        csv_saver.save(final_df, output_file)
        print(f"Arquivo CSV gerado com sucesso em: {output_file}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    main()
