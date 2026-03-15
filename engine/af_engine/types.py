from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CutoffDirection(Enum):
    BELOW = "below"  # deprived if value < cutoff (standard poverty)
    ABOVE = "above"  # deprived if value > cutoff (e.g., pollution)


class DataType(Enum):
    BINARY = "binary"
    ORDINAL = "ordinal"
    CARDINAL = "cardinal"


@dataclass
class IndicatorSpec:
    name: str
    source_column: str
    deprivation_cutoff: float
    cutoff_direction: CutoffDirection = CutoffDirection.BELOW
    weight: float = 1.0
    data_type: DataType = DataType.BINARY
    dimension: str = ""


@dataclass
class IndexConfig:
    indicators: list[IndicatorSpec]
    poverty_cutoff_k: float  # between 0 and 1
    subgroup_column: Optional[str] = None
    alpha: int = 0  # 0=M0, 1=M1, 2=M2 (future)


@dataclass
class HeadlineResults:
    H: float  # Headcount ratio (q/n)
    A: float  # Average intensity among identified
    M0: float  # Adjusted headcount ratio (H*A)
    q: int  # Number identified
    n: int  # Total observations


@dataclass
class DimensionalBreakdown:
    indicator_name: str
    dimension: str
    weight: float
    censored_headcount: float  # h_j(k)
    raw_headcount: float  # h_j (uncensored)
    contribution: float  # percentage contribution to M0
    absolute_contribution: float  # w_j * h_j(k)


@dataclass
class SubgroupResult:
    group_value: str
    n: int
    q: int
    H: float
    A: float
    M0: float
    population_share: float  # v_l = n_l / N
    poverty_share: float  # contribution to overall M0
    delta: float  # M0_l - M0_overall


@dataclass
class RobustnessResult:
    k_robustness: list[dict]  # [{k, H, A, M0}, ...]
    weight_robustness: Optional[list[dict]] = None
    leave_one_out: Optional[list[dict]] = None


@dataclass
class FullResults:
    headline: HeadlineResults
    dimensional_breakdown: list[DimensionalBreakdown]
    subgroup_results: Optional[list[SubgroupResult]] = None
    robustness: Optional[RobustnessResult] = None
    deprivation_matrix: Optional[any] = None  # numpy array
    censored_matrix: Optional[any] = None
    deprivation_scores: Optional[any] = None
    censored_scores: Optional[any] = None
