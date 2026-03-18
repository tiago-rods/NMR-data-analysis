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
INPUT_CSV_CSV = os.path.join(PROJECT_ROOT, 'quantification_comparison.csv')
INPUT_FID_CSV = os.path.join(PROJECT_ROOT, 'Data', 'Quantification', 'ASICS', 'Urina', 'quantification_bruker_fid.csv')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'Results', 'Statistics')

# Common metabolite mapping for normalization
METABOLITE_MAP = {
    'AceticAcid': 'Acetate',
    'AcetoAceticAcid': 'Acetoacetate',
    'AdipicAcid': 'Adipate',
    'BenzoicAcid': 'Benzoate',
    'CitricAcid': 'Citrate',
    'FormicAcid': 'Formate',
    'FumaricAcid': 'Fumarate',
    'GlycolicAcid': 'Glycolate',
    'HippuricAcid': 'Hippurate',
    'IsocitricAcid': 'Isocitrate',
    'LacticAcid': 'Lactate',
    'MalicAcid': 'Malate',
    'OxaloAceticAcid': 'Oxaloacetate',
    'PropionicAcid': 'Propionate',
    'PyroglutamicAcid': 'Pyroglutamate',
    'PyruvicAcid': 'Pyruvate',
    'SuccinicAcid': 'Succinate',
    'UrocanicAcid': 'Urocanate',
    '2-AminoAdipicAcid': '2-AminoAdipate',
    '2-AminobutyricAcid': '2-Aminobutyrate',
    '2-HydroxybutyricAcid': '2-Hydroxybutyrate',
    '2-HydroxyphenylAceticAcid': '2-HydroxyphenylAcetate',
    '2-MethylglutaricAcid': '2-Methylglutarate',
    '2-OxoglutaricAcid': '2-Oxoglutarate',
    '3-HydroxybutyricAcid': '3-Hydroxybutyrate',
    '3-HydroxyphenylAceticAcid': '3-HydroxyphenylAcetate',
    '3-MethyladipicAcid': '3-Methyladipate',
    '3-PhenylPropionicAcid': '3-PhenylPropionate',
    '4-AminoHippuricAcid': '4-AminoHippurate',
    '4-HydroxyphenylAceticAcid': '4-HydroxyphenylAcetate',
    '5-AminoValericAcid': '5-AminoValerate',
    'ArgininosuccinicAcid': 'Argininosuccinate',
    'NicotinicAcid': 'Nicotinate',
    'NicotinuricAcid': 'Nicotinurate',
    'PantothenicAcid': 'Pantothenate',
    'PhenylglyoxylicAcid': 'Phenylglyoxylate',
    'SyringicAcid': 'Syringate',
    'TartaricAcid': 'Tartarate',
    'ThreonicAcid': 'Threonate',
    'Trans-AcotinicAcid': 'Trans-Acotinate',
    'alpha-HydroxyisobutyricAcid': 'alpha-Hydroxyisobutyrate',
    'beta-HydroxyisovalericAcid': 'beta-Hydroxyisovalerate',
    'VanillicAcid': 'Vanillate',
    'GlutaconicAcid': 'Glutaconate',
    'MethylmalonicAcid': 'Methylmalonate',
    'Pyruvic-ate': 'Pyruvate',
    'Pyruvic-Acid': 'Pyruvate',
}

def normalize_metabolite(name):
    """Normalize metabolite names to improve matching."""
    if not isinstance(name, str):
        return name
    name = name.strip()
    
    # Remove common chiral prefixes that might be inconsistent between datasets
    if name.startswith('L-') or name.startswith('D-'):
        name = name[2:]
    
    collapsed = name.replace(' ', '')
    if collapsed in METABOLITE_MAP:
        return METABOLITE_MAP[collapsed]
    
    # Specific case fixes
    if name == 'Tryptophane': return 'Tryptophan'
    
    # Generic rule: *ic Acid -> *ate
    if name.endswith('ic Acid'):
        return name[:-7] + 'ate'
    elif name.endswith('icAcid'):
        return name[:-6] + 'ate'
    return name

def normalize_experiment(name):
    """Normalize experiment name and remove JDX extension."""
    return str(name).replace('.jdx', '').replace('_ex1_p1', '')

def load_all_data():
    """Load both CSV and FID data. Returns a combined dataframe."""
    # 1. Load CSV method (main comparison file)
    df_csv = pd.read_csv(INPUT_CSV_CSV)
    df_csv['Metodo'] = 'CSV'
    df_csv['Metabolite'] = df_csv['Metabolite'].apply(normalize_metabolite)
    
    # 2. Load FID method (Urina specific)
    df_fid_raw = pd.read_csv(INPUT_FID_CSV)
    # The FID file has different columns, need to match the main format
    df_fid = pd.DataFrame({
        'Biofluido': 'Urina',
        'Experiment': df_fid_raw['Experiment'].apply(normalize_experiment),
        'Metabolite': df_fid_raw['metabolite'].apply(normalize_metabolite),
        'Concentration_ASICS': df_fid_raw['Concentration_ASICS_Bruker_uM'],
        'Metodo': 'FID'
    })
    
    # Gold Standard for Urina FID comes from the Urina CSV GS values
    # Extract GS values (we want all 46 metabolites for each experiment)
    gs_urina = df_csv[df_csv['Biofluido'] == 'Urina'][['Experiment', 'Metabolite', 'Concentration_GS', 'HMDB']].copy()
    gs_urina['Experiment'] = gs_urina['Experiment'].apply(normalize_experiment)
    
    # To ensure even GS metabolites not identified by FID are present, use outer join
    df_fid = pd.merge(df_fid, gs_urina, on=['Experiment', 'Metabolite'], how='outer')
    # Fill in missing metadata for the newly added GS rows
    df_fid['Biofluido'] = df_fid['Biofluido'].fillna('Urina')
    df_fid['Metodo'] = df_fid['Metodo'].fillna('FID')
    df_fid['Concentration_ASICS'] = df_fid['Concentration_ASICS'].fillna(0.0)
    
    # 3. Apply experiment renaming suffixes for Urina
    # For CSV Urina
    mask_urina_csv = (df_csv['Biofluido'] == 'Urina')
    df_csv.loc[mask_urina_csv, 'Experiment'] = df_csv.loc[mask_urina_csv, 'Experiment'].apply(normalize_experiment) + '_csv'
    
    # For FID Urina
    df_fid['Experiment'] = df_fid['Experiment'] + '_fid'
    
    # Combine
    full_df = pd.concat([df_csv, df_fid], ignore_index=True)
    full_df['Concentration_ASICS'] = pd.to_numeric(full_df['Concentration_ASICS'], errors='coerce')
    full_df['Concentration_GS'] = pd.to_numeric(full_df['Concentration_GS'], errors='coerce')
    
    valid_df = full_df.dropna(subset=['Concentration_ASICS', 'Concentration_GS']).copy()
    
    return full_df, valid_df

def experiment_analysis(full_df: pd.DataFrame, valid_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-experiment correlation and error metrics."""
    rows = []
    # Group by Biofluido, Experiment and Metodo
    groups = full_df.groupby(['Biofluido', 'Experiment', 'Metodo'])

    for (biofluid, experiment, method), full_group in groups:
        # Metabolites identified by ASICS (Concentration > 0)
        asics_ident_mask = (full_group['Concentration_ASICS'].notna()) & (full_group['Concentration_ASICS'] > 0)
        n_asics = int(asics_ident_mask.sum())
        
        # Metabolites identified by GS (Concentration > 0)
        gs_ident_mask = (full_group['Concentration_GS'].notna()) & (full_group['Concentration_GS'] > 0)
        n_gs = int(gs_ident_mask.sum())
        
        # Paired data for correlations/errors (using numeric values even if 0)
        valid_group = valid_df[(valid_df['Biofluido'] == biofluid) & 
                               (valid_df['Experiment'] == experiment) & 
                               (valid_df['Metodo'] == method)]
        
        if not valid_group.empty:
            asics = valid_group['Concentration_ASICS'].values
            gs = valid_group['Concentration_GS'].values
            n_paired_calc = len(valid_group) # $N$ used for math
            
            # User defined "Pareados" as both > 0
            n_both_gt0 = int(((valid_group['Concentration_ASICS'] > 0) & (valid_group['Concentration_GS'] > 0)).sum())

            if n_paired_calc >= 3:
                # Basic check for constant values to avoid p-val warnings
                if np.var(asics) == 0 or np.var(gs) == 0:
                    pearson_r = pearson_p = spearman_r = spearman_p = np.nan
                else:
                    pearson_r, pearson_p = stats.pearsonr(asics, gs)
                    spearman_r, spearman_p = stats.spearmanr(asics, gs)
            else:
                pearson_r = pearson_p = spearman_r = spearman_p = np.nan

            mae = mean_absolute_error(gs, asics)
            mse = mean_squared_error(gs, asics)
            bias = float(np.mean(asics - gs))

            nonzero_mask = gs != 0
            if nonzero_mask.any():
                mape = float(np.mean(np.abs((asics[nonzero_mask] - gs[nonzero_mask]) / gs[nonzero_mask])) * 100)
            else:
                mape = np.nan
        else:
            n_both_gt0 = 0
            pearson_r = pearson_p = spearman_r = spearman_p = np.nan
            mae = mse = bias = mape = np.nan

        rows.append({
            'Biofluido': biofluid,
            'Experimento': experiment,
            'Metodo': method,
            'N_Metabolitos_ASICS': n_asics,
            'N_Metabolitos_GS': n_gs,
            'N_Metabolitos_Pareados': n_both_gt0,
            'Pearson_r': round(pearson_r, 6) if not np.isnan(pearson_r) else np.nan,
            'Pearson_p': round(pearson_p, 6) if not np.isnan(pearson_p) else np.nan,
            'Spearman_r': round(spearman_r, 6) if not np.isnan(spearman_r) else np.nan,
            'Spearman_p': round(spearman_p, 6) if not np.isnan(spearman_p) else np.nan,
            'MAE': round(mae, 4) if not np.isnan(mae) else np.nan,
            'MSE': round(mse, 4) if not np.isnan(mse) else np.nan,
            'MAPE': round(mape, 4) if not np.isnan(mape) else np.nan,
            'Bias': round(bias, 4) if not np.isnan(bias) else np.nan,
        })

    return pd.DataFrame(rows)

def metabolite_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-metabolite statistics including relative error."""
    rows = []
    grouped = df.groupby(['Biofluido', 'Metabolite', 'Metodo'])

    for (biofluid, metabolite, method), group in grouped:
        asics = group['Concentration_ASICS'].values
        gs = group['Concentration_GS'].values

        mean_asics = np.mean(asics)
        mean_gs = np.mean(gs)

        if mean_gs != 0:
            relative_error_pct = abs(mean_asics - mean_gs) / abs(mean_gs) * 100
        else:
            relative_error_pct = np.nan

        mae = mean_absolute_error(gs, asics)
        mse = mean_squared_error(gs, asics)

        rows.append({
            'Biofluido': biofluid,
            'Metabolite': metabolite,
            'Metodo': method,
            'Mean_ASICS': round(mean_asics, 4),
            'Mean_GS': round(mean_gs, 4),
            'Relative_Error_Pct': round(relative_error_pct, 2) if not np.isnan(relative_error_pct) else np.nan,
            'MAE': round(mae, 4),
            'MSE': round(mse, 4),
        })

    return pd.DataFrame(rows)

def build_comparison_with_diff(valid_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
    """Build a table with an absolute difference column and sorted by concentration within experiment."""
    out = full_df[['Biofluido', 'Experiment', 'Metabolite', 'HMDB',
                   'Concentration_ASICS', 'Concentration_GS', 'Metodo']].copy()
    out['Diferenca_Absoluta'] = (out['Concentration_ASICS'] - out['Concentration_GS']).abs()
    gs = out['Concentration_GS']
    out['Erro_Percentual'] = (out['Diferenca_Absoluta'] / gs.replace(0, np.nan) * 100).round(2)

    # Sort by concentration ascending within each experiment
    experiment_order = out[['Biofluido', 'Experiment', 'Metodo']].drop_duplicates()
    experiment_keys = experiment_order.apply(lambda r: (r['Biofluido'], r['Experiment'], r['Metodo']), axis=1).tolist()
    out['_exp_key'] = out.apply(lambda r: (r['Biofluido'], r['Experiment'], r['Metodo']), axis=1)
    out['_exp_key'] = pd.Categorical(out['_exp_key'], categories=experiment_keys, ordered=True)

    out = out.sort_values(
        by=['_exp_key', 'Concentration_ASICS'],
        ascending=[True, True],
    ).drop(columns=['_exp_key']).reset_index(drop=True)

    return out

def main():
    print("Loading and integrating datasets...")
    full_df, valid_df = load_all_data()

    if valid_df.empty:
        print("No valid paired data found. Exiting.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Experiment-level analysis
    print("Computing experiment correlations...")
    exp_df = experiment_analysis(full_df, valid_df)
    exp_out = os.path.join(OUTPUT_DIR, 'experiment_correlations.csv')
    exp_df.to_csv(exp_out, index=False)
    print(f"Saved experiment correlations → {exp_out}")

    # 2. Metabolite-level analysis
    print("Computing metabolite statistics...")
    met_df = metabolite_analysis(valid_df)
    met_out = os.path.join(OUTPUT_DIR, 'metabolite_statistics.csv')
    met_df.to_csv(met_out, index=False)
    print(f"Saved metabolite statistics → {met_out}")

    # 3. Comparison table with diff
    print("Building comparison with diff...")
    comp_df = build_comparison_with_diff(valid_df, full_df)
    comp_out = os.path.join(OUTPUT_DIR, 'quantification_comparison_diff.csv')
    comp_df.to_csv(comp_out, index=False)
    print(f"Saved comparison with diff → {comp_out}")

    print("\n=== Resumo Final ===")
    print(f"  Total Métodos:  {full_df['Metodo'].nunique()}")
    print(f"  Total Experimentos: {full_df['Experiment'].nunique()}")
    print(f"  Pares válidos: {len(valid_df)}")

if __name__ == '__main__':
    main()