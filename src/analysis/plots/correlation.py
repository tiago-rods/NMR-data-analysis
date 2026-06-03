"""
Módulo para geração de gráficos de dispersão (scatter plots) e correlação.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Dict
from scipy.stats import pearsonr
from src.analysis.models import PairedObservation

def plot_correlation(observations: List[PairedObservation], tool_names: Dict[int, str], output_dir: str, title: str = "Correlation Plot", filename: str = "correlation.png"):
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
    
    # Obter os IDs únicos das ferramentas presentes
    unique_tools = list(set(obs.tool_test_id for obs in observations))
    colors = sns.color_palette("husl", len(unique_tools))
    
    # Plotar cada ferramenta com uma cor diferente
    for idx, tool_id in enumerate(unique_tools):
        t_name = tool_names.get(tool_id, f"Tool {tool_id}")
        t_tools = np.array([obs.concentration_tool for obs in observations if obs.tool_test_id == tool_id])
        t_gs = np.array([obs.concentration_gs for obs in observations if obs.tool_test_id == tool_id])
        
        ax.scatter(t_gs, t_tools, alpha=0.6, edgecolors='w', s=50, color=colors[idx], label=t_name)
    
    # Regressão linear (best fit geral)
    m, b = np.polyfit(gs, tools, 1)
    
    # Definindo um limite para descartar outliers absurdos que espremem o gráfico
    # Vamos pegar o percentil 95 de todos os valores como limite superior do eixo
    max_val = np.percentile(np.concatenate([gs, tools]), 95)
    
    x_range = np.linspace(0, max_val, 100)
    ax.plot(x_range, m*x_range + b, color='blue', linestyle='--', label=f'Overall Best fit')
    
    # Linha de Identidade (y=x)
    ax.plot(x_range, x_range, color='black', linestyle='-', alpha=0.7, label='Identity (y=x)')
    
    # Cálculo de métrica rápida para legenda (geral)
    r_val, p_val = pearsonr(gs, tools)
    
    # Labels e título
    ax.set_title(title, pad=15)
    ax.set_xlabel("Gold Standard Concentration")
    ax.set_ylabel("Tool Concentration")
    
    # Ajustar as escalas dos eixos
    ax.set_xlim(-0.02 * max_val, max_val)
    ax.set_ylim(-0.02 * max_val, max_val)
    
    # Adicionando texto da correlação
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax.text(0.05, 0.95, f"Overall Pearson r: {r_val:.3f}\np-value: {p_val:.3e}", transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
            
    ax.legend(loc="lower right", frameon=True)
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico de Correlação salvo em: {output_path}")
