"""
Modelos de dados do módulo de análise estatística.

Todos os dataclasses são Value Objects — imutáveis e sem dependência
de banco de dados ou Pandas. Trafegam entre Repository e Engine livremente.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PairedObservation:
    """
    Par de concentrações (ferramenta teste vs ferramenta de referência)
    para um metabolito num espectro específico.

    Imutável (frozen=True): não pode ser modificado após criação, garantindo
    integridade dos dados ao passar entre camadas.

    Attributes:
        tool_test_id:       id_ferramenta da ferramenta em avaliação
        tool_ref_id:        id_ferramenta do Gold Standard / referência
        experiment_id:      id_experimento (espectro individual)
        metabolite_id:      id_hmdb do metabolito (CHAR 11)
        biofluid:           biofluido do experimento (ex: 'Soro', 'Urina')
        concentration_tool: concentração medida pela ferramenta teste
        concentration_gs:   concentração do Gold Standard
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
    Resultado estatístico no nível do Espectro (Experimento).
    Compara a performance da ferramenta em um único espectro contra a referência.
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


@dataclass
class StatResultMetabolito:
    """
    Resultado estatístico no nível do Metabólito.
    Avalia a precisão de quantificação de um metabólito específico agrupado por todos os espectros.
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


@dataclass
class StatResultFerramenta:
    """
    Resultado estatístico no nível global da Ferramenta.
    Avalia a performance consolidada da ferramenta em todos os espectros e metabólitos.
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

