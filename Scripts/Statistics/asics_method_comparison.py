import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ============================================================
# Paths
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

FID_CSV = os.path.join(PROJECT_ROOT, 'Data', 'Quantification', 'ASICS', 'Urina', 'quantification_bruker_fid.csv')
CSV_CSV = os.path.join(PROJECT_ROOT, 'Data', 'Quantification', 'ASICS', 'Urina', 'quantification_bruker_csv.csv')
COMPARISON_CSV = os.path.join(PROJECT_ROOT, 'Results', 'Comparison', 'quantification_comparison.csv')
OUTPUT_CSV = os.path.join(PROJECT_ROOT, 'Results', 'Statistics', 'ASICS statistics', 'asics_fid_csv_comparison.csv')

def normalize_experiment(name):
    """Normalize experiment name to 'XXRCF' format."""
    name = str(name).replace('.jdx', '').replace('_ex1_p1', '')
    return name

def normalize_metabolite(name):
    """Normalize metabolite names to improve matching."""
    if not isinstance(name, str):
        return name
    
    # 1. Standardize Case
    name = name.strip()
    
    # 2. Handle common NMR naming variations (Acid -> ate)
    mapping = {
        'AceticAcid': 'Acetate',
        'AcetoAceticAcid': 'Acetoacetate',
        'AdipicAcid': 'Adipate',
        'AzelaicAcid': 'AzelaicAcid', # Fixed later
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
    
    # Apply manual mapping first
    collapsed_name = name.replace(' ', '')
    if collapsed_name in mapping:
        name = mapping[collapsed_name]
    
    # Generic rule: *ic Acid -> *ate
    if name.endswith('ic Acid'):
        name = name[:-7] + 'ate'
    elif name.endswith('icAcid'):
        name = name[:-6] + 'ate'
        
    return name

def load_fid_data(path):
    """Load FID-based quantification data."""
    df = pd.read_csv(path)
    df['Experiment'] = df['Experiment'].apply(normalize_experiment)
    df['Metabolite'] = df['metabolite'].apply(normalize_metabolite)
    df = df.rename(columns={'Concentration_ASICS_Bruker_uM': 'Concentration_ASICS_FID'})
    # Group by normalized names in case multiple raw names map to same canonical name
    df = df.groupby(['Experiment', 'Metabolite'])['Concentration_ASICS_FID'].sum().reset_index()
    return df

def load_csv_data(path):
    """Load CSV-based quantification data (wide format)."""
    df = pd.read_csv(path)
    df = df.rename(columns={df.columns[0]: 'Metabolite'})
    df = df.melt(id_vars=['Metabolite'], var_name='Experiment', value_name='Concentration_ASICS_CSV')
    df['Experiment'] = df['Experiment'].apply(normalize_experiment)
    df['Metabolite'] = df['Metabolite'].apply(normalize_metabolite)
    df = df.groupby(['Experiment', 'Metabolite'])['Concentration_ASICS_CSV'].sum().reset_index()
    return df

def load_gs_data(path):
    """Load GS data from comparison file."""
    df = pd.read_csv(path)
    df = df[df['Biofluido'] == 'Urina'].copy()
    df['Experiment'] = df['Experiment'].apply(normalize_experiment)
    df['Metabolite'] = df['Metabolite'].apply(normalize_metabolite)
    df = df.groupby(['Experiment', 'Metabolite'])['Concentration_GS'].sum().reset_index()
    return df[['Experiment', 'Metabolite', 'Concentration_GS']]

def main():
    print("Loading datasets...")
    fid_df = load_fid_data(FID_CSV)
    csv_df = load_csv_data(CSV_CSV)
    gs_df = load_gs_data(COMPARISON_CSV)

    # Merge all datasets
    print("Merging data...")
    # Start with GS as the base if we want to compare against it, 
    # but user wants to compare "identified" metabolites, so an outer join is better.
    merged = pd.merge(fid_df, csv_df, on=['Experiment', 'Metabolite'], how='outer')
    merged = pd.merge(merged, gs_df, on=['Experiment', 'Metabolite'], how='outer')

    # Fill NaNs with 0 for concentration comparison (assuming not in list means 0 concentration)
    # However, for metric calculation we might want to keep NaNs if we only want to compare 
    # when both are present. But usually in NMR, absent = 0.
    # The user asked for "quantidade metabólitos identificados", so we count > 0.
    
    comp_df = merged.fillna(0)

    # Filter: keep only rows where at least one concentration > 0
    fid_pos = comp_df['Concentration_ASICS_FID'] > 0
    csv_pos = comp_df['Concentration_ASICS_CSV'] > 0
    gs_pos = comp_df['Concentration_GS'] > 0
    comp_df = comp_df[fid_pos | csv_pos | gs_pos].copy()

    # Calculate absolute differences and percentage errors
    print("Calculating metrics...")
    comp_df['Diff_FID_GS'] = (comp_df['Concentration_ASICS_FID'] - comp_df['Concentration_GS']).abs()
    comp_df['Diff_CSV_GS'] = (comp_df['Concentration_ASICS_CSV'] - comp_df['Concentration_GS']).abs()
    comp_df['Diff_FID_CSV'] = (comp_df['Concentration_ASICS_FID'] - comp_df['Concentration_ASICS_CSV']).abs()

    # Percentage error relative to GS (handle division by zero)
    mask = comp_df['Concentration_GS'] > 0
    comp_df['Error_FID_Pct'] = np.nan
    comp_df.loc[mask, 'Error_FID_Pct'] = (comp_df.loc[mask, 'Diff_FID_GS'] / comp_df.loc[mask, 'Concentration_GS']) * 100
    
    comp_df['Error_CSV_Pct'] = np.nan
    comp_df.loc[mask, 'Error_CSV_Pct'] = (comp_df.loc[mask, 'Diff_CSV_GS'] / comp_df.loc[mask, 'Concentration_GS']) * 100

    # Save output
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    comp_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Comparison saved to: {OUTPUT_CSV}")

    # Summary Statistics
    print("\n=== Comparison Summary ===")
    summary = []
    for exp in sorted(comp_df['Experiment'].unique()):
        subset = comp_df[comp_df['Experiment'] == exp]
        count_fid = (subset['Concentration_ASICS_FID'] > 0).sum()
        count_csv = (subset['Concentration_ASICS_CSV'] > 0).sum()
        count_gs = (subset['Concentration_GS'] > 0).sum()
        
        # Mean Absolute Error for identified pairs (subset where both exist)
        valid_fid = subset[subset['Concentration_GS'] > 0]
        mae_fid = mean_absolute_error(valid_fid['Concentration_GS'], valid_fid['Concentration_ASICS_FID']) if not valid_fid.empty else np.nan
        
        valid_csv = subset[subset['Concentration_GS'] > 0]
        mae_csv = mean_absolute_error(valid_csv['Concentration_GS'], valid_csv['Concentration_ASICS_CSV']) if not valid_csv.empty else np.nan

        summary.append({
            'Experiment': exp,
            'Identified_FID': count_fid,
            'Identified_CSV': count_csv,
            'Identified_GS': count_gs,
            'Cobertura_FID (%)': round((count_fid / count_gs) * 100, 2) if count_gs > 0 else np.nan,
            'Cobertura_CSV (%)': round((count_csv / count_gs) * 100, 2) if count_gs > 0 else np.nan,
            'MAE_FID': round(mae_fid, 2),
            'MAE_CSV': round(mae_csv, 2)
        })

    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    main()
