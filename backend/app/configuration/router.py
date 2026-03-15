from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.project import Project, ProjectStatus
from ..models.configuration import IndexConfiguration
from ..auth.router import get_current_user
from .schemas import ConfigurationCreate, ConfigurationUpdate, ConfigurationResponse

router = APIRouter()


def _get_user_project(project_id: int, db: Session, current_user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/configuration", response_model=ConfigurationResponse, status_code=status.HTTP_201_CREATED)
def create_configuration(
    project_id: int,
    data: ConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)

    # Remove old configuration if exists
    old_config = db.query(IndexConfiguration).filter(
        IndexConfiguration.project_id == project_id
    ).first()
    if old_config:
        db.delete(old_config)
        db.flush()

    dimensions_data = [dim.model_dump() for dim in data.dimensions]

    config = IndexConfiguration(
        project_id=project_id,
        poverty_cutoff_k=data.poverty_cutoff_k,
        subgroup_column=data.subgroup_column,
        dimensions=dimensions_data,
    )
    db.add(config)

    # Update project status
    project.status = ProjectStatus.CONFIGURED
    project.current_step = max(project.current_step, 3)

    db.commit()
    db.refresh(config)
    return config


@router.get("/projects/{project_id}/configuration", response_model=ConfigurationResponse)
def get_configuration(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    config = db.query(IndexConfiguration).filter(
        IndexConfiguration.project_id == project_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="No configuration found for this project")
    return config


@router.put("/projects/{project_id}/configuration", response_model=ConfigurationResponse)
def update_configuration(
    project_id: int,
    data: ConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, db, current_user)
    config = db.query(IndexConfiguration).filter(
        IndexConfiguration.project_id == project_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="No configuration found for this project")

    if data.poverty_cutoff_k is not None:
        config.poverty_cutoff_k = data.poverty_cutoff_k
    if data.subgroup_column is not None:
        config.subgroup_column = data.subgroup_column
    if data.dimensions is not None:
        config.dimensions = [dim.model_dump() for dim in data.dimensions]

    db.commit()
    db.refresh(config)
    return config
