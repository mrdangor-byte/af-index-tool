import os
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.project import Project
from ..models.dataset import Dataset
from ..auth.router import get_current_user
from ..config import settings
from .schemas import DatasetResponse, DataPreviewResponse, ColumnsResponse, ColumnMetadata

router = APIRouter()


def _get_user_project(project_id: int, db: Session, current_user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _build_column_metadata(df: pd.DataFrame) -> list[dict]:
    metadata = []
    for col in df.columns:
        info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique()),
            "min": None,
            "max": None,
            "mean": None,
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            info["min"] = float(df[col].min()) if not df[col].isna().all() else None
            info["max"] = float(df[col].max()) if not df[col].isna().all() else None
            info["mean"] = float(df[col].mean()) if not df[col].isna().all() else None
        metadata.append(info)
    return metadata


def _read_datafile(file_path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Read CSV or Excel file. For Excel, uses specified sheet, or auto-detects best sheet."""
    ext = str(file_path).rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(file_path)
    # Excel: if sheet_name given, use it
    if sheet_name:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    # Auto-detect: prefer sheets with "clean" or "data" in name, otherwise largest
    xls = pd.ExcelFile(file_path)
    if len(xls.sheet_names) == 1:
        return pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    # Try to find a "cleaned" or "data" sheet
    for name in xls.sheet_names:
        lower = name.lower()
        if "clean" in lower and "data" in lower:
            return pd.read_excel(xls, sheet_name=name)
    for name in xls.sheet_names:
        lower = name.lower()
        if "clean" in lower or lower in ("data", "dataset"):
            return pd.read_excel(xls, sheet_name=name)
    # Fallback: pick largest
    best_sheet = None
    best_rows = -1
    for name in xls.sheet_names:
        df_tmp = pd.read_excel(xls, sheet_name=name)
        if len(df_tmp) > best_rows:
            best_rows = len(df_tmp)
            best_sheet = name
    return pd.read_excel(xls, sheet_name=best_sheet)


@router.post("/projects/{project_id}/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)

    # Validate file type
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files are accepted",
        )

    # Save file to disk
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = upload_dir / unique_name

    contents = file.file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Parse with pandas
    try:
        if ext == "csv":
            df = pd.read_csv(file_path)
        else:
            df = _read_datafile(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}",
        )

    column_metadata = _build_column_metadata(df)

    # Remove old dataset if exists
    old_dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    if old_dataset:
        if os.path.exists(old_dataset.file_path):
            os.remove(old_dataset.file_path)
        db.delete(old_dataset)
        db.flush()

    dataset = Dataset(
        project_id=project_id,
        original_filename=filename,
        file_path=str(file_path),
        row_count=len(df),
        column_metadata=column_metadata,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/projects/{project_id}/data/preview", response_model=DataPreviewResponse)
def preview_data(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset uploaded for this project")

    df = _read_datafile(dataset.file_path)

    preview_df = df.head(20)
    # Replace NaN with None for JSON serialization
    rows = preview_df.where(preview_df.notna(), None).to_dict(orient="records")
    return DataPreviewResponse(
        columns=list(df.columns),
        rows=rows,
        total_rows=len(df),
    )


@router.get("/projects/{project_id}/data/columns", response_model=ColumnsResponse)
def get_columns(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset uploaded for this project")

    columns = [ColumnMetadata(**col) for col in dataset.column_metadata]
    return ColumnsResponse(columns=columns)
