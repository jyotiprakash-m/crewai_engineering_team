from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import SQLModel, Field, Session, select, func
import shutil
import os
from pydantic import BaseModel
from engineering_team.utils.database import get_session


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    requirements: str
    module_name: str
    class_name: str
    project_name: str
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column_kwargs={"onupdate": func.now()}, 
        nullable=False
    )
    
class ProjectCreate(BaseModel):
    requirements: str
    module_name: str
    class_name: str
    project_name: str
    
# Initialize the API router for projects
router = APIRouter(prefix="/projects", tags=["Projects"])

#=============================
# Router endpoints
#=============================

@router.post("/", response_model=Project)
def add_project(
    project: ProjectCreate,
    session: Session = Depends(get_session)
):
    return create_project(session, project)

@router.get("/", response_model=list[Project])
def get_projects(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    session: Session = Depends(get_session)
):
    return fetch_projects(session, project_name)

@router.get("/{project_id}", response_model=Project)
def get_project_by_id(
    project_id: int,
    session: Session = Depends(get_session)
):
    return fetch_project_by_id(session, project_id)

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    return delete_project_by_id(session, project_id)

#=============================
# Service functions
#=============================

def create_project(session: Session, project_data: ProjectCreate) -> Project:
    """
    Create a new project.
    """
    # Check if project_name already exists
    existing = session.exec(
        select(Project).where(Project.project_name == project_data.project_name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Project with name '{project_data.project_name}' already exists.")
    new_project = Project(
        requirements=project_data.requirements,
        module_name=project_data.module_name,
        class_name=project_data.class_name,
        project_name=project_data.project_name,
    )
    session.add(new_project)
    session.commit()
    session.refresh(new_project)
    return new_project

def fetch_projects(session: Session, project_name: Optional[str] = None) -> List[Project]:
    """
    Fetch all projects, optionally filtered by project_name (case-insensitive, partial match).
    """
    query = select(Project)
    if project_name:
        query = query.where(func.lower(Project.project_name).like(f"%{project_name.lower()}%"))
    return list(session.exec(query).all())

def fetch_project_by_id(session: Session, project_id: int) -> Optional[Project]:
    """
    Fetch a single project by its ID.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found.")
    return project

def delete_project_by_id(session: Session, project_id: int) -> dict:
    """
    Delete a project by its ID and remove its associated directory and files.
    """
    project = session.get(Project, project_id)
    if project:
        # Delete the project directory if it exists
        project_dir = os.path.join("output", project.project_name)
        if os.path.exists(project_dir) and os.path.isdir(project_dir):
            shutil.rmtree(project_dir)
        session.delete(project)
        session.commit()
        return {"detail": f"Project with id {project_id} and directory '{project.project_name}' deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found.")

