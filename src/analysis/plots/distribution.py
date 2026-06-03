"""
Módulo para geração de gráficos de distribuição (Boxplots / Violin Plots) dos erros.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from typing import List
from src.analysis.models import PairedObservation

def plot_bias_distribution(observations: List[PairedObservation], output_dir: str, title: str = "Bias Distribution", filename: str = "bias_distribution.png", by: str = "metabolite"):
    """
    Gera um Boxplot da distribuição do Bias (Ferramenta - GS).
    Se by="metabolite", agrupa por metabólito. Se by="biofluid", agrupa por biofluido.
    """
    if not observations:
        return

    # Preparar DataFrame para o Seaborn
    data = []
    for obs in observations:
        bias = obs.concentration_tool - obs.concentration_gs
        data.append({
            "Metabolite": obs.metabolite_id,
            "Biofluid": obs.biofluid,
            "Bias": bias
        })
    df = pd.DataFrame(data)

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    
    # Ajuste do tamanho dinâmico dependendo da quantidade de categorias
    group_col = "Metabolite" if by == "metabolite" else "Biofluid"
    n_cats = df[group_col].nunique()
    fig, ax = plt.subplots(figsize=(max(8, n_cats * 0.5), 6))
    
    # Criar Boxplot
    sns.boxplot(data=df, x=group_col, y="Bias", ax=ax, palette="Set2")
    # Opcional: adicionar stripplot sobreposto para ver os pontos individuais
    sns.stripplot(data=df, x=group_col, y="Bias", color=".3", size=3, alpha=0.5, ax=ax)
    
    # Linha zero de referência (sem erro)
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, label='Zero Bias')
    
    ax.set_title(title, pad=15)
    ax.set_xlabel(group_col)
    ax.set_ylabel("Bias (Tool - GS)")
    plt.xticks(rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico de Distribuição salvo em: {output_path}")
