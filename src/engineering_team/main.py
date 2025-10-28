#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engineering_team.crew import Coder
import uvicorn

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()

class CoderInput(BaseModel):
    assignment: str

@app.post("/run-coder/")
async def run_coder(input: CoderInput):
    try:
        result = Coder().crew().kickoff(inputs={"assignment": input.assignment})
        return {"result": result.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8000, reload=True)
