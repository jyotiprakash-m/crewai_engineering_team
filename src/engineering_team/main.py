#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engineering_team.crew import EngineeringTeam
import uvicorn

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()

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
        result = EngineeringTeam().crew().kickoff(inputs={"requirements": input.requirements, "module_name": input.module_name, "class_name": input.class_name, "project_name": input.project_name})
        return {"result": result.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8000, reload=True)
