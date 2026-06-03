"""
PlotManager - Facade para geração de todos os gráficos estatísticos.
"""
import os
from typing import List, Dict
from src.analysis.models import PairedObservation, StatResultFerramenta
from src.analysis.plots.bland_altman import plot_bland_altman
from src.analysis.plots.correlation import plot_correlation
from src.analysis.plots.distribution import plot_bias_distribution
from src.analysis.plots.performance_metrics import plot_precision_recall_space, plot_global_metrics_bar

class PlotManager:
    """
    Orquestra a geração de gráficos.
    Recebe os dados brutos e resultados estatísticos e aciona os módulos de plotagem.
    """
    def __init__(self, output_base_dir: str = "outputs/plots"):
        self.output_dir = output_base_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_plots(self, 
                           observations: List[PairedObservation], 
                           global_results: List[StatResultFerramenta],
                           tool_names: Dict[int, str]):
        """
        Gera todos os gráficos de uma vez.
        
        Args:
            observations: Lista de todas as observações emparelhadas (para scatter, bland-altman e distribuição).
            global_results: Lista de resultados por ferramenta (para performance e PR space).
            tool_names: Dicionário mapeando ID da ferramenta para Nome, para legendas.
        """
        print("Iniciando geração de gráficos...")
        
        # 1. Gráficos baseados em PairedObservations (dependem de valores contínuos)
        if observations:
            plot_bland_altman(observations, self.output_dir)
            plot_correlation(observations, tool_names, self.output_dir)
            
            # Distribuição por metabólito e por biofluido
            plot_bias_distribution(observations, self.output_dir, title="Bias by Metabolite", filename="bias_by_metabolite.png", by="metabolite")
            plot_bias_distribution(observations, self.output_dir, title="Bias by Biofluid", filename="bias_by_biofluid.png", by="biofluid")
        else:
            print("Nenhuma PairedObservation fornecida. Pulando Bland-Altman, Scatter e Distribuição.")

        # 2. Gráficos baseados em resultados globais (Classification / Performance)
        if global_results:
            plot_precision_recall_space(global_results, tool_names, self.output_dir)
            plot_global_metrics_bar(global_results, tool_names, self.output_dir)
        else:
            print("Nenhum StatResultFerramenta fornecido. Pulando gráficos de performance global.")

        print(f"Geração de gráficos concluída. Arquivos salvos em {self.output_dir}")

