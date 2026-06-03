"""
Módulo para geração de gráficos de dispersão (scatter plots) e correlação.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List
from scipy.stats import pearsonr
from src.analysis.models import PairedObservation

def plot_correlation(observations: List[PairedObservation], output_dir: str, title: str = "Correlation Plot", filename: str = "correlation.png"):
    """
    Gera um gráfico de dispersão com linha de identidade (y=x) e reta de regressão.
    Salva o gráfico em png/pdf na pasta output_dir.
    """
    if not observations:
        return

    tools = np.array([obs.concentration_tool for obs in observations])
    gs = np.array([obs.concentration_gs for obs in observations])

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot principal
    ax.scatter(gs, tools, alpha=0.6, edgecolors='w', s=50)
    
    # Regressão linear (best fit)
    m, b = np.polyfit(gs, tools, 1)
    x_range = np.linspace(min(gs.min(), tools.min()), max(gs.max(), tools.max()), 100)
    ax.plot(x_range, m*x_range + b, color='blue', linestyle='--', label=f'Best fit: y={m:.2f}x+{b:.2f}')
    
    # Linha de Identidade (y=x)
    ax.plot(x_range, x_range, color='black', linestyle='-', alpha=0.7, label='Identity (y=x)')
    
    # Cálculo de métrica rápida para legenda
    r_val, p_val = pearsonr(gs, tools)
    
    # Labels e título
    ax.set_title(title, pad=15)
    ax.set_xlabel("Gold Standard Concentration")
    ax.set_ylabel("Tool Concentration")
    
    # Adicionando texto da correlação
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax.text(0.05, 0.95, f"Pearson r: {r_val:.3f}\np-value: {p_val:.3e}", transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
            
    ax.legend(loc="lower right", frameon=True)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico de Correlação salvo em: {output_path}")
