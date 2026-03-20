import pandas as pd
import numpy as np
import os
import glob
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Configuration
MAGMET_DIR = r'c:\Iniciacao Cientifica\Data_Analysis\NMR-data-analysis\Data\Quantification\MagMet\Soro'
GS_FILE = r'c:\Iniciacao Cientifica\Data_Analysis\NMR-data-analysis\quantification_comparison.csv'
OUTPUT_DIR = r'c:\Iniciacao Cientifica\Data_Analysis\NMR-data-analysis\Results\Statistics\MagMet'

METABOLITE_MAP = {
    'AceticAcid': 'Acetate', 'AcetoAceticAcid': 'Acetoacetate', 'AdipicAcid': 'Adipate',
    'BenzoicAcid': 'Benzoate', 'CitricAcid': 'Citrate', 'FormicAcid': 'Formate',
    'FumaricAcid': 'Fumarate', 'GlycolicAcid': 'Glycolate', 'HippuricAcid': 'Hippurate',
    'IsocitricAcid': 'Isocitrate', 'LacticAcid': 'Lactate', 'MalicAcid': 'Malate',
    'OxaloAceticAcid': 'Oxaloacetate', 'PropionicAcid': 'Propionate', 'PyroglutamicAcid': 'Pyroglutamate',
    'PyruvicAcid': 'Pyruvate', 'SuccinicAcid': 'Succinate', 'UrocanicAcid': 'Urocanate',
    'ArgininosuccinicAcid': 'Argininosuccinate', 'Tryptophane': 'Tryptophan',
}

def normalize_metabolite(name):
    """Normalize metabolite names to improve matching."""
    if not isinstance(name, str): return name
    name = name.strip()
    
    # Remove chiral prefixes
    if name.startswith('L-') or name.startswith('D-'):
        name = name[2:]
        
    # Handle "ic acid" or "icacid" conversion to "ate"
    if name.endswith('ic acid') or name.endswith('ic Acid'):
        name = name[:-7] + 'ate'
    elif name.endswith('icacid') or name.endswith('icAcid'):
        name = name[:-6] + 'ate'
    # Generic " acid" suffix
    elif name.endswith(' acid') or name.endswith(' Acid'):
        name = name[:-5] + 'ate'
        
    collapsed = name.replace(' ', '')
    if collapsed in METABOLITE_MAP:
        return METABOLITE_MAP[collapsed]
        
    return name

def parse_magmet_file(filepath):
    """Parse a MagMet CSV file, extracting experiment name from header."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
        # Line 2 is usually the FID name: # FID: 1_1H.fid
        fid_line = lines[1].strip()
        experiment = fid_line.replace('# FID: ', '').replace('.fid', '').strip()
        
    # Read the data table starting from line 11 (header is line 10)
    df = pd.read_csv(filepath, skiprows=9) # skips 0-9, header is line 10 (index 9)
    return experiment, df

def load_data():
    """Load MagMet files and Gold Standard data."""
    # 1. Load Gold Standard (Soro)
    df_gs_raw = pd.read_csv(GS_FILE)
    gs_soro = df_gs_raw[df_gs_raw['Biofluido'] == 'Soro'].copy()
    gs_soro['Metabolite'] = gs_soro['Metabolite'].apply(normalize_metabolite)
    
    # 2. Load MagMet files
    magmet_dfs = []
    files = glob.glob(os.path.join(MAGMET_DIR, '*.csv'))
    
    for f in files:
        experiment, df_m = parse_magmet_file(f)
        df_m = df_m.rename(columns={
            'Compound Name': 'Metabolite',
            'Concentration (µM)': 'Concentration_MagMet',
            'HMDB ID': 'HMDB_MagMet'
        })
        df_m['Experiment'] = experiment
        df_m['Metabolite'] = df_m['Metabolite'].apply(normalize_metabolite)
        magmet_dfs.append(df_m[['Experiment', 'Metabolite', 'Concentration_MagMet', 'HMDB_MagMet']])
        
    df_magmet = pd.concat(magmet_dfs, ignore_index=True)
    
    # 3. Merge with Gold Standard
    # Get unique (Experiment, Metabolite) pairs from GS
    gs_base = gs_soro[['Experiment', 'Metabolite', 'Concentration_GS', 'HMDB']].copy()
    
    # Outer join to ensure we have all GS metabolites and all MagMet metabolites
    combined = pd.merge(df_magmet, gs_base, on=['Experiment', 'Metabolite'], how='outer')
    
    combined['Concentration_MagMet'] = combined['Concentration_MagMet'].fillna(0.0)
    combined['Biofluido'] = 'Soro'
    combined['Metodo'] = 'MagMet'
    
    # Filter for valid numeric pairs
    combined['Concentration_MagMet'] = pd.to_numeric(combined['Concentration_MagMet'], errors='coerce')
    combined['Concentration_GS'] = pd.to_numeric(combined['Concentration_GS'], errors='coerce')
    
    valid = combined.dropna(subset=['Concentration_MagMet', 'Concentration_GS']).copy()
    
    return combined, valid

def run_statistics(full_df, valid_df):
    """Run per-experiment and per-metabolite statistics."""
    # Experiment Stats
    exp_rows = []
    for (bio, exp), group in full_df.groupby(['Biofluido', 'Experiment']):
        n_magmet = int((group['Concentration_MagMet'] > 0).sum())
        n_gs = int((group['Concentration_GS'] > 0).sum())
        
        valid_group = valid_df[(valid_df['Experiment'] == exp)]
        n_paired = int(((valid_group['Concentration_MagMet'] > 0) & (valid_group['Concentration_GS'] > 0)).sum())
        
        # Calculation N: for math we use all shared metabolites (including 0s)
        asics = valid_group['Concentration_MagMet'].values
        gs = valid_group['Concentration_GS'].values
        
        if len(valid_group) >= 3 and np.var(asics) > 0 and np.var(gs) > 0:
            pearson_r, pearson_p = stats.pearsonr(asics, gs)
            spearman_r, spearman_p = stats.spearmanr(asics, gs)
        else:
            pearson_r = pearson_p = spearman_r = spearman_p = np.nan
            
        mae = mean_absolute_error(gs, asics) if len(valid_group) > 0 else np.nan
        mse = mean_squared_error(gs, asics) if len(valid_group) > 0 else np.nan
        bias = np.mean(asics - gs) if len(valid_group) > 0 else np.nan
        
        nonzero_mask = gs > 0
        if nonzero_mask.any():
            mape = np.mean(np.abs((asics[nonzero_mask] - gs[nonzero_mask]) / gs[nonzero_mask])) * 100
        else:
            mape = np.nan
            
        exp_rows.append({
            'Biofluido': bio, 'Experimento': exp, 'Metodo': 'MagMet',
            'N_Metabolitos_MagMet': n_magmet, 'N_Metabolitos_GS': n_gs, 'N_Metabolitos_Pareados': n_paired,
            'Pearson_r': pearson_r, 'Pearson_p': pearson_p, 'Spearman_r': spearman_r, 'Spearman_p': spearman_p,
            'MAE': mae, 'MSE': mse, 'MAPE': mape, 'Bias': bias
        })
        
    df_exp = pd.DataFrame(exp_rows)
    
    # Metabolite Stats
    met_rows = []
    for metabolite, group in valid_df.groupby('Metabolite'):
        asics = group['Concentration_MagMet'].values
        gs = group['Concentration_GS'].values
        n_experiments = len(group)
        
        if n_experiments >= 3 and np.var(asics) > 0 and np.var(gs) > 0:
            pearson_r, _ = stats.pearsonr(asics, gs)
        else:
            pearson_r = np.nan
            
        mae = mean_absolute_error(gs, asics)
        avg_gs = np.mean(gs)
        rel_mae = (mae / avg_gs * 100) if avg_gs > 0 else np.nan
        
        met_rows.append({
            'Metabolite': metabolite, 'Metodo': 'MagMet', 'N_Experimentos': n_experiments,
            'Pearson_r': pearson_r, 'MAE': mae, 'Rel_MAE_%': rel_mae, 'Avg_GS': avg_gs
        })
        
    df_met = pd.DataFrame(met_rows)
    
    return df_exp, df_met

if __name__ == '__main__':
    print('Starting MagMet Soro FID Analysis...')
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    full, valid = load_data()
    print(f'Loaded {len(full)} rows, {len(valid)} valid pairs.')
    
    df_exp, df_met = run_statistics(full, valid)
    
    # Save Results
    df_exp.to_csv(os.path.join(OUTPUT_DIR, 'experiment_correlations.csv'), index=False)
    df_met.to_csv(os.path.join(OUTPUT_DIR, 'metabolite_statistics.csv'), index=False)
    
    # Full Diff Table
    full['Diff_Abs'] = np.abs(full['Concentration_MagMet'] - full['Concentration_GS'])
    full['Diff_Perc'] = (full['Diff_Abs'] / full['Concentration_GS'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Sort by concentration within experiment
    full = full.sort_values(by=['Experiment', 'Concentration_MagMet'], ascending=[True, True])
    full.to_csv(os.path.join(OUTPUT_DIR, 'quantification_comparison_diff.csv'), index=False)
    
    print(f'Results saved to {OUTPUT_DIR}')
