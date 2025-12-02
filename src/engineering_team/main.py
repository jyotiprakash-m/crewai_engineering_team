#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engineering_team.crew import EngineeringTeam
import uvicorn
from fastapi.staticfiles import StaticFiles
from typing import List
from fastapi.responses import FileResponse
from engineering_team.utils.database import init_db,engine
from fastapi.concurrency import asynccontextmanager

from engineering_team.routers.core_functionality_router import router as core_functionality_router
from engineering_team.routers.project_router import router as project_router
from sqlmodel import  Field, Session, select
from sqlalchemy.exc import SQLAlchemyError
from engineering_team.routers.project_router import Project
from fastapi.middleware.cors import CORSMiddleware

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up db...")
    init_db()   # Initialize the database
    yield
    print("🛑 Shutting down db...")

app = FastAPI(title="Engineering Team API", description="API for managing engineering team projects", lifespan=lifespan)

# =========================================
# 🌐 CORS Middleware (for Next.js frontend)
# =========================================
# You can update `origins` later to your frontend’s actual domain
origins = [
    "http://98.94.14.94:3000",
    "https://jyotidev.in",
    "http://jyotidev.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # or ["*"] for all (less secure)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.router.redirect_slashes = False

# Mount static files for serving zipped projects
app.mount("/public", StaticFiles(directory="output"), name="public")

# Default input values for testing
requirements = """
A todo application in Python that allows users to add, view, update, and delete tasks.
"""
module_name = "app.py"
class_name = "Todo"
project_name = "todo_manager"

class EngineeringInput(BaseModel):
    requirements: str = requirements
    module_name: str = module_name
    class_name: str = class_name
    project_name: str = project_name

@app.post("/run-engineering/")
async def run_engineering(input: EngineeringInput):
    try:
        # Check if a project with the same name already exists
        with Session(engine) as session:
            existing = session.exec(
                select(Project).where(Project.project_name == input.project_name)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Project with name '{input.project_name}' already exists."
                )

        result = EngineeringTeam().crew().kickoff(inputs={
            "requirements": input.requirements,
            "module_name": input.module_name,
            "class_name": input.class_name,
            "project_name": input.project_name
        })
        
        # Store the project in the database after successful creation of the project files
        with Session(engine) as session:
            new_project = Project(
                requirements=input.requirements,
                module_name=input.module_name,
                class_name=input.class_name,
                project_name=input.project_name
            )
            session.add(new_project)
            session.commit()
            session.refresh(new_project)
        
        return {"result": new_project, "message": "Engineering task completed and project stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(core_functionality_router)
app.include_router(project_router)

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8001, reload=True)
