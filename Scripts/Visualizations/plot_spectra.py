import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_overlaid_spectra(csv_file, title):
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo não encontrado - {csv_file}")
        return

    print(f"Carregando dados de {csv_file}...")
    df = pd.read_csv(csv_file)
    
    if 'PPM' not in df.columns:
        print(f"Erro: Coluna 'PPM' não encontrada no arquivo {csv_file}.")
        return

    ppm = df['PPM']
    
    plt.figure(figsize=(14, 7))
    
    # Plota cada experimento (coluna) contra o PPM
    experiments = [col for col in df.columns if col != 'PPM']
    
    print(f"Plotando {len(experiments)} espectros...")
    for col in experiments:
        plt.plot(ppm, df[col], label=col, linewidth=0.8, alpha=0.8)

    # Configurações do gráfico
    # Em RMN, o eixo X (PPM) geralmente cresce da direita para a esquerda
    plt.gca().invert_xaxis() 
    
    plt.xlabel('Deslocamento Químico (ppm)', fontsize=12)
    plt.ylabel('Intensidade', fontsize=12)
    plt.title(title, fontsize=14)
    
    # Opcional: Mostrar legenda se não houver muitos experimentos (limite arbitrário de 20 para não poluir)
    if len(experiments) <= 20:
        plt.legend(loc='upper right', fontsize=8, bbox_to_anchor=(1.15, 1))
        
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    soro_file = os.path.join('Data', 'csv', 'Soro', 'LNBio_Soro.csv')
    urina_file = os.path.join('Data', 'csv', 'Urina', 'LNBio_Urina.csv')
    
    # Plota os dados de Soro
    if os.path.exists(soro_file):
        plot_overlaid_spectra(soro_file, 'Espectros Sobrepostos - Soro')
    else:
        print(f"Aviso: {soro_file} não existe.")
        
    # Plota os dados de Urina
    if os.path.exists(urina_file):
        plot_overlaid_spectra(urina_file, 'Espectros Sobrepostos - Urina')
    else:
        print(f"Aviso: {urina_file} não existe.")
