"""
Módulo para geração de gráficos Bland-Altman.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List
from src.analysis.models import PairedObservation

def plot_bland_altman(observations: List[PairedObservation], output_dir: str, title: str = "Bland-Altman Plot", filename: str = "bland_altman.png"):
    """
    Gera um gráfico de Bland-Altman a partir de uma lista de PairedObservations.
    Salva o gráfico em png/pdf na pasta output_dir.
    """
    if not observations:
        return

    # Extrai as concentrações
    tools = np.array([obs.concentration_tool for obs in observations])
    gs = np.array([obs.concentration_gs for obs in observations])

    # Cálculos para Bland-Altman
    means = (tools + gs) / 2
    diffs = tools - gs
    
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    upper_limit = mean_diff + 1.96 * std_diff
    lower_limit = mean_diff - 1.96 * std_diff

    # Configuração de estilo do Seaborn para viés acadêmico
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot principal
    ax.scatter(means, diffs, alpha=0.6, edgecolors='w', s=50)
    
    # Linhas de viés e limites de concordância
    ax.axhline(mean_diff, color='red', linestyle='--', linewidth=2, label=f'Mean Bias: {mean_diff:.2f}')
    ax.axhline(upper_limit, color='gray', linestyle=':', linewidth=2, label=f'+1.96 SD: {upper_limit:.2f}')
    ax.axhline(lower_limit, color='gray', linestyle=':', linewidth=2, label=f'-1.96 SD: {lower_limit:.2f}')
    ax.axhline(0, color='black', linestyle='-', linewidth=1) # Linha zero de referência
    
    # Labels e título
    ax.set_title(title, pad=15)
    ax.set_xlabel("Mean Concentration (Tool & GS)")
    ax.set_ylabel("Difference (Tool - GS)")
    ax.legend(loc="upper right", frameon=True)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico Bland-Altman salvo em: {output_path}")
