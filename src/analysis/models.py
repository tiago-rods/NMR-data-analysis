"""
Data models for the statistical analysis module.

All dataclasses are Value Objects—immutable and without database or Pandas
dependency. They flow freely between Repository and Engine.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PairedObservation:
    """
    Pair of concentrations (test tool vs reference tool)
    for a specific metabolite in a specific spectrum.

    Immutable (frozen=True): cannot be modified after creation, ensuring
    data integrity when passing between layers.

    Attributes:
        tool_test_id:       id_ferramenta of the tool being evaluated
        tool_ref_id:        id_ferramenta of the Gold Standard / reference tool
        experiment_id:      id_experimento (individual spectrum)
        metabolite_id:      id_hmdb of the metabolite (CHAR 11)
        biofluid:           biofluid of the experiment (e.g., 'Soro', 'Urina')
        concentration_tool: concentration measured by the test tool
        concentration_gs:   concentration of the Gold Standard
    """

    tool_test_id: int
    tool_ref_id: int
    experiment_id: int
    metabolite_id: str
    biofluid: str
    concentration_tool: float
    concentration_gs: float


@dataclass
class StatResultEspectro:
    """
    Statistical result at the Spectrum (Experiment) level.
    Compares the tool's performance in a single spectrum against the reference.
    """
    tool_test_id: int
    tool_ref_id: int
    experiment_id: int
    biofluid: str
    gs_total_metabolitos: int = 0
    tool_total_metabolitos: int = 0
    match_count: int = 0
    coverage_pct: float = 0.0
    identified_gs_pct: float = 0.0
    pearson_r: float = 0.0
    pearson_p: float = 0.0
    spearman_r: float = 0.0
    spearman_p: float = 0.0
    bias: float = 0.0
    mse: float = 0.0
    mape: float = 0.0
    precisao: float = 0.0
    recall: float = 0.0
    

@dataclass
class StatResultMetabolito:
    """
    Statistical result at the Metabolite level.
    Evaluates the quantification accuracy of a specific metabolite across all spectra.
    """
    tool_test_id: int
    tool_ref_id: int
    metabolite_id: str
    n_observations: int = 0
    pearson_r: float = 0.0
    pearson_p: float = 0.0
    spearman_r: float = 0.0
    spearman_p: float = 0.0
    bias: float = 0.0
    mse: float = 0.0
    mape: float = 0.0
    precisao: float = 0.0 
    recall: float = 0.0



@dataclass
class StatResultFerramenta:
    """
    Statistical result at the global Tool level.
    Evaluates the consolidated performance of the tool across all spectra and metabolites.
    """
    tool_test_id: int
    tool_ref_id: int
    n_observations: int = 0
    coverage_mean_pct: float = 0.0
    identified_gs_mean_pct: float = 0.0
    pearson_r: float = 0.0
    pearson_p: float = 0.0
    spearman_r: float = 0.0
    spearman_p: float = 0.0
    bias: float = 0.0
    mse: float = 0.0
    mape: float = 0.0
    precisao: float = 0.0
    recall: float = 0.0

