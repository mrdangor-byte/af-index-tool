from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class HeadlineResultSchema(BaseModel):
    H: float
    A: float
    M0: float
    q: int
    n: int


class DimensionalBreakdownSchema(BaseModel):
    indicator_name: str
    dimension: str
    weight: float
    censored_headcount: float
    raw_headcount: float
    contribution: float
    absolute_contribution: float


class SubgroupResultSchema(BaseModel):
    group_value: str
    n: int
    q: int
    H: float
    A: float
    M0: float
    population_share: float
    poverty_share: float
    delta: float


class AnalysisResultResponse(BaseModel):
    id: int
    project_id: int
    H: Optional[float] = None
    A: Optional[float] = None
    M0: Optional[float] = None
    q: Optional[int] = None
    n: Optional[int] = None
    dimensional_breakdown: Optional[List[dict]] = None
    subgroup_decomposition: Optional[List[dict]] = None
    robustness_results: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RobustnessResponse(BaseModel):
    k_robustness: List[dict]
    weight_robustness: Optional[List[dict]] = None
    leave_one_out: Optional[List[dict]] = None
