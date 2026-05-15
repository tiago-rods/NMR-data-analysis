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
class StatResult:
    """
    Resultado estatístico calculado para um conjunto de PairedObservations.

    A granularidade é indicada pelos campos opcionais:
      - experiment_id preenchido + biofluid preenchido → por espectro
      - experiment_id=None + biofluid preenchido        → por ferramenta + biofluido
      - experiment_id=None + biofluid=None              → por ferramenta (total)

    Attributes:
        tool_test_id:      id_ferramenta da ferramenta em avaliação
        tool_ref_id:       id_ferramenta do Gold Standard
        metabolite_id:     id_hmdb do metabolito analisado
        experiment_id:     id_experimento; None para resultados agregados
        biofluid:          biofluido; None para agregação total
        pearson_r:         coeficiente de correlação de Pearson [-1, 1]
        pearson_p:         p-valor da correlação de Pearson [0, 1]
        spearman_r:        coeficiente de correlação de Spearman [-1, 1]
        spearman_p:        p-valor da correlação de Spearman [0, 1]
        bias:              viés médio (mean(tool - gs))
        mse:               erro quadrático médio (≥ 0)
        mape:              erro percentual absoluto médio (≥ 0)
        coverage_pct:      % de metabolitos do GS identificados pela ferramenta [0, 100]
        identified_gs_pct: % de metabolitos identificados em relação ao GS [0, 100]
        n_observations:    número de pares usados no cálculo
    """

    tool_test_id: int
    tool_ref_id: int
    metabolite_id: str
    experiment_id: Optional[int] = None
    biofluid: Optional[str] = None

    # Métricas de correlação
    pearson_r: float = 0.0
    pearson_p: float = 0.0
    spearman_r: float = 0.0
    spearman_p: float = 0.0

    # Métricas de erro
    bias: float = 0.0
    mse: float = 0.0
    mape: float = 0.0

    # Métricas de cobertura (para dados_metabolitos)
    coverage_pct: float = 0.0
    identified_gs_pct: float = 0.0

    # Diagnóstico
    n_observations: int = 0
