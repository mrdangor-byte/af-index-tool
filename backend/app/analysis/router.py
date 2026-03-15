import sys
from pathlib import Path
from dataclasses import asdict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Add engine to path — works in Docker (engine mounted at /app/engine)
sys.path.insert(0, "/app/engine")
# Also works locally (engine is sibling directory)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "engine"))
from af_engine import compute_index, IndexConfig, IndicatorSpec, CutoffDirection, DataType
from af_engine.robustness import run_robustness

from ..database import get_db
from ..models.user import User
from ..models.project import Project, ProjectStatus
from ..models.dataset import Dataset
from ..models.configuration import IndexConfiguration
from ..models.result import AnalysisResult
from ..auth.router import get_current_user
from .schemas import AnalysisResultResponse, RobustnessResponse

router = APIRouter()


def _get_user_project(project_id: int, db: Session, current_user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _load_dataset(db: Session, project_id: int) -> pd.DataFrame:
    dataset = db.query(Dataset).filter(Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="No dataset uploaded for this project")
    from ..data.router import _read_datafile
    return _read_datafile(dataset.file_path)


def _build_engine_config(config: IndexConfiguration) -> IndexConfig:
    indicators = []
    for dim in config.dimensions:
        dim_name = dim["name"]
        for ind in dim["indicators"]:
            direction = CutoffDirection(ind.get("cutoff_direction", "below"))
            data_type = DataType(ind.get("data_type", "binary"))
            indicators.append(
                IndicatorSpec(
                    name=ind["name"],
                    source_column=ind["source_column"],
                    deprivation_cutoff=ind["deprivation_cutoff"],
                    cutoff_direction=direction,
                    weight=ind["weight"],
                    data_type=data_type,
                    dimension=dim_name,
                )
            )
    return IndexConfig(
        indicators=indicators,
        poverty_cutoff_k=config.poverty_cutoff_k,
        subgroup_column=config.subgroup_column,
    )


@router.post("/projects/{project_id}/analyze", response_model=AnalysisResultResponse)
def run_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)

    config = db.query(IndexConfiguration).filter(
        IndexConfiguration.project_id == project_id
    ).first()
    if not config:
        raise HTTPException(status_code=400, detail="No configuration found for this project")

    df = _load_dataset(db, project_id)
    engine_config = _build_engine_config(config)

    # If subgroup_column contains dashes, treat as composite (e.g. "Faculty-Gender-Race")
    if engine_config.subgroup_column and "-" in engine_config.subgroup_column:
        parts = engine_config.subgroup_column.split("-")
        missing = [p for p in parts if p not in df.columns]
        if not missing:
            df[engine_config.subgroup_column] = df[parts].astype(str).agg("-".join, axis=1)

    try:
        results = compute_index(df, engine_config, include_robustness=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")

    dim_breakdown = [asdict(d) for d in results.dimensional_breakdown]
    subgroup_data = None
    if results.subgroup_results:
        subgroup_data = [asdict(s) for s in results.subgroup_results]

    # Remove old results if they exist
    old_result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    if old_result:
        db.delete(old_result)
        db.flush()

    analysis_result = AnalysisResult(
        project_id=project_id,
        H=results.headline.H,
        A=results.headline.A,
        M0=results.headline.M0,
        q=results.headline.q,
        n=results.headline.n,
        dimensional_breakdown=dim_breakdown,
        subgroup_decomposition=subgroup_data,
    )
    db.add(analysis_result)

    project.status = ProjectStatus.ANALYZED
    project.current_step = max(project.current_step, 4)

    db.commit()
    db.refresh(analysis_result)
    return analysis_result


@router.get("/projects/{project_id}/results", response_model=AnalysisResultResponse)
def get_results(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="No results found. Run analysis first.")
    return result


@router.post("/projects/{project_id}/robustness", response_model=RobustnessResponse)
def run_robustness_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)

    config = db.query(IndexConfiguration).filter(
        IndexConfiguration.project_id == project_id
    ).first()
    if not config:
        raise HTTPException(status_code=400, detail="No configuration found for this project")

    df = _load_dataset(db, project_id)
    engine_config = _build_engine_config(config)

    if engine_config.subgroup_column and "-" in engine_config.subgroup_column:
        parts = engine_config.subgroup_column.split("-")
        missing = [p for p in parts if p not in df.columns]
        if not missing:
            df[engine_config.subgroup_column] = df[parts].astype(str).agg("-".join, axis=1)

    try:
        robustness = run_robustness(df, engine_config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Robustness analysis failed: {str(e)}")

    robustness_data = asdict(robustness)

    # Update stored results with robustness data
    result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    if result:
        result.robustness_results = robustness_data
        db.commit()

    return RobustnessResponse(**robustness_data)
