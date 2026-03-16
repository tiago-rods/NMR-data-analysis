
# TODO: Ler tabela csv e adquirir dados da tabela, 
# Dados utéis: experimento, metabólito, Concentração ASICS, Concentração GS
# Após a aquisição dos dados, fazer análise estatística   - Biofluido, Experimento, N° Metabolitos, Correlação de Pearson, Correlação de Spearman, p_Pearson, p_Spearman
# - Com experimentos 
#   - Correlação de pearson da quantificação 
#   - Correlação de Spearman da quantificação
#   - Quantidade de metabólitos Identificados por experimento, (Média, Desvio Padrão, Mediana) (ASICS em comparação com GS)
#   - Tabela com métricas de Erros (MAE, MSE)
#
# - Com metabólitos 
#   - Adicionar Erro relativo na quantificação de metabólitos na tabela, 
#
# - Fazer tabela csv com:
#   - Biofluido, Experimento, N° Metabolitos, Correlação de Pearson, Correlação de Spearman, p_Pearson, p_Spearman

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import warnings
# ============================================================
# Paths
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
INPUT_CSV = os.path.join(PROJECT_ROOT, 'quantification_comparison.csv')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'Results', 'Statistics')


def load_data(path: str):
    """Load quantification_comparison.csv. Returns (full_df, valid_paired_df)."""
    df = pd.read_csv(path)
    df['Concentration_ASICS'] = pd.to_numeric(df['Concentration_ASICS'], errors='coerce')
    df['Concentration_GS'] = pd.to_numeric(df['Concentration_GS'], errors='coerce')
    valid = df.dropna(subset=['Concentration_ASICS', 'Concentration_GS']).copy()
    print(f"Total records: {len(df)}  |  Valid paired records: {len(valid)}")
    return df, valid


# ============================================================
# Análise por Experimento
# ============================================================
def experiment_analysis(full_df: pd.DataFrame, valid_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-experiment correlation and error metrics."""
    rows = []

    # Count metabolites identified by ASICS (concentration > 0) per experiment
    full_grouped = full_df.groupby(['Biofluido', 'Experiment'])
    valid_grouped = valid_df.groupby(['Biofluido', 'Experiment'])

    for (biofluid, experiment), full_group in full_grouped:
        # ASICS-identified: Concentration_ASICS > 0 (non-NaN and non-zero)
        n_asics = int(((full_group['Concentration_ASICS'].notna()) & (full_group['Concentration_ASICS'] > 0)).sum())
        # GS-identified: Concentration_GS is not NaN
        n_gs = int(full_group['Concentration_GS'].notna().sum())

        # Paired data for correlations/errors
        if (biofluid, experiment) in valid_grouped.groups:
            group = valid_grouped.get_group((biofluid, experiment))
            asics = group['Concentration_ASICS'].values
            gs = group['Concentration_GS'].values
            n_paired = len(group)

            if n_paired >= 3:
                pearson_r, pearson_p = stats.pearsonr(asics, gs)
                spearman_r, spearman_p = stats.spearmanr(asics, gs)
            else:
                pearson_r = pearson_p = spearman_r = spearman_p = np.nan

            mae = mean_absolute_error(gs, asics)
            mse = mean_squared_error(gs, asics)
            bias = float(np.mean(asics - gs))

            # MAPE: avoid division by zero
            nonzero_mask = gs != 0
            if nonzero_mask.any():
                mape = float(np.mean(np.abs((asics[nonzero_mask] - gs[nonzero_mask]) / gs[nonzero_mask])) * 100)
            else:
                mape = np.nan
        else:
            n_paired = 0
            pearson_r = pearson_p = spearman_r = spearman_p = np.nan
            mae = mse = bias = mape = np.nan

        rows.append({
            'Biofluido': biofluid,
            'Experimento': experiment,
            'N_Metabolitos_ASICS': n_asics,
            'N_Metabolitos_GS': n_gs,
            'N_Metabolitos_Pareados': n_paired,
            'Pearson_r': round(pearson_r, 6) if not np.isnan(pearson_r) else np.nan,
            'Pearson_p': round(pearson_p, 6) if not np.isnan(pearson_p) else np.nan,
            'Spearman_r': round(spearman_r, 6) if not np.isnan(spearman_r) else np.nan,
            'Spearman_p': round(spearman_p, 6) if not np.isnan(spearman_p) else np.nan,
            'MAE': round(mae, 4) if not np.isnan(mae) else np.nan,
            'MSE': round(mse, 4) if not np.isnan(mse) else np.nan,
            'MAPE': round(mape, 4) if not np.isnan(mape) else np.nan,
            'Bias': round(bias, 4) if not np.isnan(bias) else np.nan,
        })

    result = pd.DataFrame(rows)
    return result


def print_experiment_summary(exp_df: pd.DataFrame):
    """Print descriptive statistics of metabolite count per biofluid."""
    print("\n=== Estatísticas descritivas: N° de metabólitos por biofluido ===")
    for bf in exp_df['Biofluido'].unique():
        subset = exp_df[exp_df['Biofluido'] == bf]['N_Metabolitos_Pareados']
        print(f"\n  {bf} (metabólitos pareados):")
        print(f"    Média:         {subset.mean():.2f}")
        print(f"    Desvio Padrão: {subset.std():.2f}")
        print(f"    Mediana:       {subset.median():.1f}")
        print(f"    Min:           {subset.min()}")
        print(f"    Max:           {subset.max()}")
        print(f"    N° Experimentos: {len(subset)}")


# ============================================================
# Análise por Metabólito
# ============================================================
def metabolite_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-metabolite statistics including relative error."""
    rows = []
    grouped = df.groupby(['Biofluido', 'Metabolite'])

    for (biofluid, metabolite), group in grouped:
        asics = group['Concentration_ASICS'].values
        gs = group['Concentration_GS'].values
        n = len(group)

        mean_asics = np.mean(asics)
        mean_gs = np.mean(gs)

        # Relative error (%)
        if mean_gs != 0:
            relative_error_pct = abs(mean_asics - mean_gs) / abs(mean_gs) * 100
        else:
            relative_error_pct = np.nan

        mae = mean_absolute_error(gs, asics)
        mse = mean_squared_error(gs, asics)

        rows.append({
            'Biofluido': biofluid,
            'Metabolite': metabolite,
            'Mean_ASICS': round(mean_asics, 4),
            'Mean_GS': round(mean_gs, 4),
            'Relative_Error_Pct': round(relative_error_pct, 2) if not np.isnan(relative_error_pct) else np.nan,
            'MAE': round(mae, 4),
            'MSE': round(mse, 4),
        })

    result = pd.DataFrame(rows)
    return result


def build_comparison_with_diff(valid_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
    """Build a table like quantification_comparison with an absolute difference column."""
    # Start from the full dataframe to keep all rows
    out = full_df[['Biofluido', 'Experiment', 'Metabolite', 'HMDB',
                   'Concentration_ASICS', 'Concentration_GS']].copy()
    out['Diferenca_Absoluta'] = (out['Concentration_ASICS'] - out['Concentration_GS']).abs()
    # Percentage error: |ASICS - GS| / GS * 100  (NaN when GS is 0 or missing)
    gs = out['Concentration_GS']
    out['Erro_Percentual'] = (out['Diferenca_Absoluta'] / gs.replace(0, np.nan) * 100).round(2)
    return out


# ============================================================
# Main
# ============================================================
def main():
    # 1. Load data
    print(f"Reading: {INPUT_CSV}")
    full_df, valid_df = load_data(INPUT_CSV)

    if valid_df.empty:
        print("No valid paired data found. Exiting.")
        return

    # 2. Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 3. Experiment-level analysis
    exp_df = experiment_analysis(full_df, valid_df)
    exp_out = os.path.join(OUTPUT_DIR, 'experiment_correlations.csv')
    exp_df.to_csv(exp_out, index=False)
    print(f"\nSaved experiment correlations → {exp_out}")
    print_experiment_summary(exp_df)

    # 4. Metabolite-level analysis
    met_df = metabolite_analysis(valid_df)
    met_out = os.path.join(OUTPUT_DIR, 'metabolite_statistics.csv')
    met_df.to_csv(met_out, index=False)
    print(f"\nSaved metabolite statistics → {met_out}")

    # 5. Comparison table with absolute difference
    comp_df = build_comparison_with_diff(valid_df, full_df)
    comp_out = os.path.join(OUTPUT_DIR, 'quantification_comparison_diff.csv')
    comp_df.to_csv(comp_out, index=False)
    print(f"\nSaved comparison with diff → {comp_out}")

    # 6. Quick summary
    print("\n=== Resumo Geral ===")
    print(f"  Biofluidos:   {valid_df['Biofluido'].nunique()}")
    print(f"  Experimentos: {valid_df['Experiment'].nunique()}")
    print(f"  Metabólitos:  {valid_df['Metabolite'].nunique()}")
    print(f"  Pares válidos: {len(valid_df)}")

    print("\n=== Tabela de Correlações por Experimento (preview) ===")
    print(exp_df.to_string(index=False))

    print("\n=== Tabela de Metabólitos (preview - top 10 por erro relativo) ===")
    top_err = met_df.dropna(subset=['Relative_Error_Pct']).nlargest(10, 'Relative_Error_Pct')
    print(top_err.to_string(index=False))


if __name__ == '__main__':
    main()
