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
A simple account management system for a trading simulation platform.
The system should allow users to create an account, deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
 from buying more shares than they can afford, or selling shares that they don't have.
 The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
"""
module_name = "accounts.py"
class_name = "Account"

class EngineeringInput(BaseModel):
    requirements: str = requirements
    module_name: str = module_name
    class_name: str = class_name

@app.post("/run-engineering/")
async def run_engineering(input: EngineeringInput):
    try:
        result = EngineeringTeam().crew().kickoff(inputs={"requirements": input.requirements, "module_name": input.module_name, "class_name": input.class_name})
        return {"result": result.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# If you want to run this file directly
if __name__ == "__main__":
    uvicorn.run("engineering_team.main:app", host="0.0.0.0", port=8000, reload=True)
