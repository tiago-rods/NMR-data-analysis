import pytest
import pandas as pd
from pathlib import Path
from src.readers.csv_reader import CSVReader
from src.cleaners.nmRanalysis_cleaner import NmRanalysisCleaner
from src.cleaners.ASICS_cleaner import ASICSCleaner
from src.cleaners.MagMet_cleaner import MagMetCleaner

def test_integridade_dados_reais_nmranalysis():
    # 1. Definição do caminho do dado real
    caminho_real = Path("data/raw/nmRanalysis/LNBio06_nmRanalysis_Soro_csv_size6.csv")
    
    # Verificamos primeiro se o arquivo existe (para não dar erro de caminho)
    assert caminho_real.exists(), f"Arquivo não encontrado em: {caminho_real}"
    
    # 2. Testando a LEITURA
    reader = CSVReader()
    df_bruto = reader.read(str(caminho_real))
    
    # Check de integridade básico: O arquivo não pode estar vazio
    assert not df_bruto.empty
    
    # Check de colunas: O Cleaner precisa dessas colunas para funcionar
    colunas_obrigatorias = ["Sample", "Metabolite", "Quantity", "Fitting Error"]
    for col in colunas_obrigatorias:
        assert col in df_bruto.columns, f"A coluna '{col}' está faltando no arquivo real!"

def test_processamento_completo_com_dados_reais():
    caminho_real = "data/raw/nmRanalysis/LNBio06_nmRanalysis_Soro_csv_size6.csv"
    
    reader = CSVReader()
    cleaner = NmRanalysisCleaner()
    
    # Fluxo completo: Lê e Limpa
    df_bruto = reader.read(caminho_real)
    df_limpo = cleaner.clean(df_bruto)
    
    # Verificações pós-limpeza:
    # 1. Não deve haver mais duplicatas de (Sample, Base_Metabolite)
    duplicatas = df_limpo.duplicated(subset=["Sample", "Base_Metabolite"]).sum()
    assert duplicatas == 0, f"Encontradas {duplicatas} duplicatas após a limpeza!"
    
    # 2. Os nomes das amostras não devem começar com 'X' (regra do seu cleaner)
    assert not df_limpo["Sample"].str.startswith("X").any()

def test_integridade_dados_reais_asics():
    caminho_real = Path("data/raw/ASICS/Soro/quantification_serum.csv")
    assert caminho_real.exists()
    
    reader = CSVReader()
    cleaner = ASICSCleaner()
    
    df_bruto = reader.read(str(caminho_real), index_col=0) # ASICS costuma ter o índice na primeira coluna
    df_limpo = cleaner.clean(df_bruto)
    
    # Verificação: O índice deve se chamar 'metabolite'
    assert df_limpo.index.name == "metabolite"
    
    # Verificação: Não deve haver aspas nos nomes das colunas (amostras)
    assert not any('"' in str(col) for col in df_limpo.columns)

def test_integridade_dados_reais_magmet():
    # Usando o arquivo 02 como amostra
    caminho_real = Path("data/raw/MagMet/magmet_LNBio_Ag_Se_02.csv")
    assert caminho_real.exists()
    
    reader = CSVReader()
    cleaner = MagMetCleaner()
    
    df_bruto = reader.read(str(caminho_real))
    df_limpo = cleaner.clean(df_bruto)
    
    # Verificação: A coluna HMDB ID deve ter sido removida
    assert "HMDB ID" not in df_limpo.columns
    
    # Verificação: O índice deve ser 'metabolite'
    assert df_limpo.index.name == "metabolite"
    
    # Verificação: Sufixos .fid removidos das colunas
    assert not any(".fid" in str(col) for col in df_limpo.columns)
