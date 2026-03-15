from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ColumnMetadata(BaseModel):
    name: str
    dtype: str
    missing_count: int
    unique_count: int
    min: Optional[Any] = None
    max: Optional[Any] = None
    mean: Optional[float] = None


class DatasetResponse(BaseModel):
    id: int
    project_id: int
    original_filename: str
    row_count: int
    column_metadata: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DataPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[dict]
    total_rows: int


class ColumnsResponse(BaseModel):
    columns: List[ColumnMetadata]
