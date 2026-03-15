from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IndicatorSchema(BaseModel):
    name: str
    source_column: str
    deprivation_cutoff: float
    cutoff_direction: str = "below"  # "below" or "above"
    weight: float = 1.0
    data_type: str = "binary"  # "binary", "ordinal", "cardinal"


class DimensionSchema(BaseModel):
    name: str
    indicators: List[IndicatorSchema]


class ConfigurationCreate(BaseModel):
    poverty_cutoff_k: float
    subgroup_column: Optional[str] = None
    dimensions: List[DimensionSchema]


class ConfigurationUpdate(BaseModel):
    poverty_cutoff_k: Optional[float] = None
    subgroup_column: Optional[str] = None
    dimensions: Optional[List[DimensionSchema]] = None


class ConfigurationResponse(BaseModel):
    id: int
    project_id: int
    poverty_cutoff_k: float
    subgroup_column: Optional[str] = None
    dimensions: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
