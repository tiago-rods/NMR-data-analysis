import pandas as pd
import pytest
from src.cleaners.ASICS_cleaner import ASICSCleaner
from src.cleaners.gold_standard_cleaner import GoldStandardCleaner

@pytest.fixture
def asics_long_df():
    """DataFrame in long format with decimal commas."""
    data = {
        "Experiment": ["01RCF", "01RCF", "02RCF"],
        "Metabolite": ["Alanine", "Glucose", "Alanine"],
        "Concentration_uM_Final": ["100,5", "200,0", "150,0"]
    }
    return pd.DataFrame(data)

def test_asics_cleaner_long_decimal_conversion(asics_long_df):
    cleaner = ASICSCleaner()
    cleaned = cleaner.clean(asics_long_df.copy())
    # After cleaning, concentration column should be float dtype
    assert cleaned["Concentration_uM_Final"].dtype == float
    # Values should be correctly converted
    expected = [100.5, 200.0, 150.0]
    assert cleaned["Concentration_uM_Final"].tolist() == expected

@pytest.fixture
def asics_wide_df():
    """Wide format typical of ASICS output (samples as columns)."""
    cols = ["metabolite", "01RCF_ex1_p1", "01RCF_ex2_p1"]
    rows = [
        ["Alanine", 100.5, 110.0],
        ["Glucose", 200.0, 210.0]
    ]
    return pd.DataFrame(rows, columns=cols)

def test_asics_cleaner_wide_retains_columns(asics_wide_df):
    cleaner = ASICSCleaner()
    cleaned = cleaner.clean(asics_wide_df.copy())
    # Wide format should keep metabolite column name unchanged and retain all sample columns
    assert "metabolite" in cleaned.columns
    assert "01RCF_ex1_p1" in cleaned.columns
    assert cleaned.shape[0] == 2

@pytest.fixture
def gold_standard_raw_df():
    """Simulate raw Excel after GoldStandardCleaner processing (first column contains .cnx filenames)."""
    data = {
        "Sample": ["01RCF_ex1_p1.cnx", "01RCF_ex2_p1.cnx"],
        "metabolite1": [1.0, 2.0],
        "metabolite2": [3.0, 4.0]
    }
    return pd.DataFrame(data)

def test_gold_standard_cleaner_removes_cnx_suffix(gold_standard_raw_df):
    cleaner = GoldStandardCleaner()
    cleaned = cleaner.clean(gold_standard_raw_df.copy())
    # Sample column should have .cnx suffix removed
    assert all(not s.endswith('.cnx') for s in cleaned['Sample'])
    # Column names should stay the same (except Sample rename)
    assert "Sample" in cleaned.columns
    assert "metabolite1" in cleaned.columns
    assert cleaned.shape[0] == 2
