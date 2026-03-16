import pandas as pd
import os

def standardize_experiment(name):
    if not isinstance(name, str):
        return str(name)
    return name.replace('.jdx', '').replace('.cnx', '').strip()

def standardize_metabolite(name):
    if not isinstance(name, str):
        return str(name)
    name = name.strip()
    
    # Specific known ASICS -> GS mappings based on typical discrepancies
    mapping = {
        'D-Glucose': 'Glucose',
        'L-Lactate': 'Lactate',
        'L-Alanine': 'Alanine',
        'L-Glutamine': 'Glutamine',
        'L-GlutamicAcid': 'Glutamate',
        'L-Valine': 'Valine',
        'L-Leucine': 'Leucine',
        'L-Isoleucine': 'Isoleucine',
        'L-Proline': 'Proline',
        'L-Histidine': 'Histidine',
        'L-Tyrosine': 'Tyrosine',
        'L-Phenylalanine': 'Phenylalanine',
        'L-Tryptophane': 'Tryptophan',
        'L-Serine': 'Serine',
        'L-Threonine': 'Threonine',
        'L-Methionine': 'Methionine',
        'L-Cysteine': 'Cysteine',
        'L-Lysine': 'Lysine',
        'L-Arginine': 'Arginine',
        'L-Aspartate': 'Aspartate',
        'L-Asparagine': 'Asparagine',
        'L-Glycine': 'Glycine',
        'GlycolicAcid': 'Glycolate',
        'AceticAcid': 'Acetate',
        'CitricAcid': 'Citrate',
        'MalicAcid': 'Malate',
        'FormicAcid': 'Formate',
        'Pyruvic-Acid': 'Pyruvate',
        'PyruvicAcid': 'Pyruvate',
        'SuccinicAcid': 'Succinate',
        'FumaricAcid': 'Fumarate',
        'GlycericAcid': 'Glycerate',
        'AscorbicAcid': 'Ascorbate',
        'UricAcid': 'Urate'
    }
    
    if name in mapping:
        return mapping[name]
        
    if name.endswith('icAcid'): return name[:-6] + 'ate'
    elif name.endswith('ic acid'): return name[:-7] + 'ate'
    elif name.endswith('Acid'): return name[:-4] + 'ate'
    
    # Try stripping D- or L- prefixes if they still don't match
    if name.startswith('L-') or name.startswith('D-'):
        return name[2:]
        
    return name

def process_asics(filepath, biofluido):
    if not os.path.exists(filepath):
        print(f"Warning: ASICS file not found: {filepath}")
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    df = df.rename(columns={'Unnamed: 0': 'Metabolite'})
    df_long = pd.melt(df, id_vars=['Metabolite'], var_name='Experiment', value_name='Concentration_ASICS')
    
    df_long['Experiment'] = df_long['Experiment'].apply(standardize_experiment)
    df_long['Metabolite'] = df_long['Metabolite'].apply(standardize_metabolite)
    df_long['Biofluido'] = biofluido
    return df_long

def process_gs(filepath, biofluido):
    if not os.path.exists(filepath):
        print(f"Warning: GS file not found: {filepath}")
        return pd.DataFrame()
    
    # Read without header to find structure
    df_raw = pd.read_excel(filepath, header=None)
    
    # 1. Identify rows
    met_row_idx = 2 # Usually row 2 contains metabolites
    data_start_idx = -1
    hmdb_row_idx = -1
    
    for i in range(len(df_raw)):
        first_val = str(df_raw.iloc[i, 0]).strip()
        if first_val == 'HMDB Accession Number':
            hmdb_row_idx = i
        if '.cnx' in first_val or '.jdx' in first_val:
            if data_start_idx == -1:
                data_start_idx = i

    if data_start_idx == -1:
        print(f"Error: Could not find data rows in {filepath}")
        return pd.DataFrame()

    # 2. Extract Metabolites
    metabolites = df_raw.iloc[met_row_idx].fillna('').astype(str).tolist()
    # The first column is labels (Experiment name), metabolites start at index 1
    met_names = [standardize_metabolite(m) for m in metabolites[1:]]
    
    # 3. Extract Data
    data_rows = []
    for i in range(data_start_idx, len(df_raw)):
        row = df_raw.iloc[i].tolist()
        exp_name = standardize_experiment(row[0])
        values = row[1:]
        for met, val in zip(met_names, values):
            data_rows.append({
                'Experiment': exp_name,
                'Metabolite': met,
                'Concentration_GS': val,
                'Biofluido': biofluido
            })
            
    df_long = pd.DataFrame(data_rows)
    df_long['Concentration_GS'] = pd.to_numeric(df_long['Concentration_GS'], errors='coerce')
    
    # 4. Extract HMDB if exists
    hmdb_mapping = {}
    if hmdb_row_idx != -1:
        hmdb_row = df_raw.iloc[hmdb_row_idx].fillna('').astype(str).tolist()[1:]
        for met, hmdb in zip(met_names, hmdb_row):
            if hmdb and hmdb != 'nan':
                hmdb_mapping[met] = hmdb
                
    return df_long.dropna(subset=['Concentration_GS']), hmdb_mapping

def main():
    base_dir = "Data/Quantification"
    biofluids = ["Soro", "Urina"]
    all_data = []
    global_hmdb = {}
    
    for bf in biofluids:
        asics_path = os.path.join(base_dir, "ASICS", bf, f"quantification_{bf}.csv")
        gs_path = os.path.join(base_dir, "Gold_Standard", bf, "concentrations.xlsx")
        
        print(f"Processing {bf}...")
        df_asics = process_asics(asics_path, bf)
        df_gs, hmdb_map = process_gs(gs_path, bf)
        
        if df_asics.empty or df_gs.empty:
            continue
            
        global_hmdb.update(hmdb_map)
        
        # Merge
        merged = pd.merge(df_asics, df_gs, on=['Biofluido', 'Experiment', 'Metabolite'], how='left')
        all_data.append(merged)
        
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df['HMDB'] = final_df['Metabolite'].map(global_hmdb)
        
        # Reorder columns
        cols = ['Biofluido', 'Experiment', 'Metabolite', 'HMDB', 'Concentration_ASICS', 'Concentration_GS']
        final_df = final_df[cols]
        
        out_file = "quantification_comparison.csv"
        final_df.to_csv(out_file, index=False)
        print(f"Generated {out_file} with {len(final_df)} records.")
        
        # Diagnostics
        valid_rows = final_df.dropna(subset=['Concentration_ASICS', 'Concentration_GS'])
        print(f"Records with BOTH values: {len(valid_rows)}")
        print(f"Total HMDB codes mapped: {final_df['HMDB'].notna().sum()}")
        
        # Check a specific one for the user
        target_exp = '05RCF_ex1_p1'
        test_rows = valid_rows[valid_rows['Experiment'] == target_exp]
        print(f"Experiment {target_exp} has {len(test_rows)} metabolites matched.")

if __name__ == "__main__":
    main()
