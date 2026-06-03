"""
Módulo para geração de gráficos de performance global (Precision-Recall scatter, Bar charts).
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from typing import List, Dict
from src.analysis.models import StatResultFerramenta

def plot_precision_recall_space(results: List[StatResultFerramenta], tool_names: Dict[int, str], output_dir: str, title: str = "Precision-Recall Space", filename: str = "precision_recall.png"):
    """
    Plota os pontos no espaço Precision-Recall para cada ferramenta.
    Como a maioria das ferramentas (exceto MagMet) não possui threshold contínuo, 
    usamos o par (Recall, Precision) como um classificador binário único.
    """
    if not results:
        return

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Criar paleta de cores para as ferramentas
    colors = sns.color_palette("husl", len(results))
    
    for idx, r in enumerate(results):
        tool_name = tool_names.get(r.tool_test_id, f"Tool {r.tool_test_id}")
        ax.scatter(r.recall, r.precisao, label=tool_name, color=colors[idx], s=150, edgecolor='k')
        # Adicionar o nome da ferramenta próximo ao ponto
        ax.text(r.recall + 0.02, r.precisao, tool_name, fontsize=10, va='center')

    # Limites ideais
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    
    # Linha de isolinha F1 (opcional, desenhar algumas curvas de nível de F1-score)
    delta = 0.01
    x = np.arange(0.01, 1.05, delta)
    y = np.arange(0.01, 1.05, delta)
    X, Y = np.meshgrid(x, y)
    Z = 2 * (X * Y) / (X + Y)
    CS = ax.contour(X, Y, Z, levels=[0.2, 0.4, 0.6, 0.8, 0.9], colors='gray', alpha=0.3, linestyles='dashed')
    ax.clabel(CS, inline=True, fontsize=8, fmt='F1=%.1f')

    ax.set_title(title, pad=15)
    ax.set_xlabel("Recall (Sensitivity)")
    ax.set_ylabel("Precision (PPV)")
    ax.legend(loc="lower left", frameon=True)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico Precision-Recall salvo em: {output_path}")


def plot_global_metrics_bar(results: List[StatResultFerramenta], tool_names: Dict[int, str], output_dir: str, title: str = "Global Metrics Comparison", filename: str = "global_metrics.png"):
    """
    Gera um gráfico de barras comparando Precisão, Recall e Cobertura entre as ferramentas.
    """
    if not results:
        return

    data = []
    for r in results:
        t_name = tool_names.get(r.tool_test_id, f"Tool {r.tool_test_id}")
        data.append({"Tool": t_name, "Metric": "Precision", "Value": r.precisao})
        data.append({"Tool": t_name, "Metric": "Recall", "Value": r.recall})
        data.append({"Tool": t_name, "Metric": "Coverage (%)", "Value": r.coverage_mean_pct / 100.0}) # Normalizar para 0-1

    df = pd.DataFrame(data)

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.barplot(data=df, x="Tool", y="Value", hue="Metric", ax=ax, palette="viridis")
    
    ax.set_title(title, pad=15)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.legend(title="Metric", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico de Métricas Globais salvo em: {output_path}")
