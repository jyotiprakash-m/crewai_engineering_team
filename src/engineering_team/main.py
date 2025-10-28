#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engineering_team.crew import StockPicker
import uvicorn

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()

class StockPickerInput(BaseModel):
    sector: str
    current_date:str = datetime.now().strftime("%Y-%m-%d")

@app.post("/run-stock-picker/")
async def run_stock_picker(input: StockPickerInput):
    try:
        result = StockPicker().crew().kickoff(inputs={"sector": input.sector, "current_date": input.current_date})
        return {"result": result.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8000, reload=True)
