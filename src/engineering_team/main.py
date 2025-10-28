#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engineering_team.crew import ResearchCrew
import uvicorn

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()

class ResearchInput(BaseModel):
    company: str

@app.post("/run-financial_researcher/")
async def run_financial_researcher(input: ResearchInput):
    try:
        result = ResearchCrew().crew().kickoff(inputs={"company": input.company})
        return {"result": result.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8000, reload=True)
