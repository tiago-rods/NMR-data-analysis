import os
import sys
from database.db_manager import DataBaseManager
from src.analysis.stats_calculator import StatsCalculator
from src.analysis.stats_engine import StatsEngine
from src.analysis.plots.plot_manager import PlotManager

def main() -> None:
    """Main entry point for calculating statistics and generating plots.

    Fetches paired data and experiment counts from the database,
    calculates statistics across different analysis tools, and
    generates the final plots.
    """
    # 1. Obter dados do banco e calcular métricas
    print("Conectando ao banco e calculando estatísticas...")
    db = DataBaseManager()
    calculator = StatsCalculator(db)
    engine = StatsEngine()

    observations = calculator.fetch_paired_data()
    counts = calculator.fetch_all_experiment_counts()
    metabolite_counts = calculator.fetch_all_metabolite_counts()
    
    # results é uma tupla: (espectros, metabolitos, ferramentas)
    results = engine.calculate_all(observations, counts, metabolite_counts)
    _, _, ferramentas_resultados = results

    # 2. Configurar nomes de ferramentas reais vindos do banco de dados
    tool_names_dict = {
        2: "ASICS (fid)",
        3: "ASICS (csv)",
        4: "nmRanalysis",
        5: "MagMet",
        6: "LNBioGS"
    }

    # 3. Gerar Gráficos
    print("\nGerando gráficos...")
    plotter = PlotManager(output_base_dir="outputs/graficos_finais")
    plotter.generate_all_plots(observations, ferramentas_resultados, tool_names_dict)

if __name__ == "__main__":
    # Adiciona o diretório raiz ao PYTHONPATH para evitar ModuleNotFoundError
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
