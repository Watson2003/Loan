import os
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Base Directory Setup
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "loan_model.pkl"

# Initialize FastAPI App
app = FastAPI(title="LuxeLoan AI Predictor")

# Mount Static Files Directory
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount Templates Directory
templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Global Model Variable
MODEL = None

def load_prediction_model():
    global MODEL
    if MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run training first.")
        MODEL = joblib.load(MODEL_PATH)
    return MODEL

# Define Pydantic Schema for Input Validation
class LoanRequest(BaseModel):
    no_of_dependents: int = Field(..., ge=0, le=10, description="Number of dependents of the applicant")
    education: str = Field(..., description="Graduate or Not Graduate")
    self_employed: str = Field(..., description="Yes or No")
    income_annum: float = Field(..., ge=0, description="Annual income of the applicant")
    loan_amount: float = Field(..., ge=0, description="Loan amount requested")
    loan_term: int = Field(..., ge=1, description="Loan term in months")
    cibil_score: int = Field(..., ge=300, le=900, description="CIBIL Credit Score")
    residential_assets_value: float = Field(..., ge=0, description="Value of residential assets")
    commercial_assets_value: float = Field(..., ge=0, description="Value of commercial assets")
    luxury_assets_value: float = Field(..., ge=0, description="Value of luxury assets")
    bank_asset_value: float = Field(..., ge=0, description="Value of bank assets")

@app.on_event("startup")
def startup_event():
    # Load model on startup to cache it
    try:
        load_prediction_model()
        print("Model loaded successfully on startup.")
    except Exception as e:
        print(f"Warning: Startup model loading failed: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/predict", response_class=JSONResponse)
async def predict_loan(payload: LoanRequest):
    try:
        model = load_prediction_model()
        
        # Prepare inputs as a pandas DataFrame matching feature names
        input_data = {
            "no_of_dependents": [payload.no_of_dependents],
            "education": [payload.education],
            "self_employed": [payload.self_employed],
            "income_annum": [payload.income_annum],
            "loan_amount": [payload.loan_amount],
            "loan_term": [payload.loan_term],
            "cibil_score": [payload.cibil_score],
            "residential_assets_value": [payload.residential_assets_value],
            "commercial_assets_value": [payload.commercial_assets_value],
            "luxury_assets_value": [payload.luxury_assets_value],
            "bank_asset_value": [payload.bank_asset_value]
        }
        
        input_df = pd.DataFrame(input_data)
        
        # Run prediction
        raw_prediction = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
        
        # Probability of approval (class 1)
        approval_probability = float(probabilities[1])
        
        decision = "Approved" if raw_prediction == 1 else "Rejected"
        
        # Calculate interesting financial indicators to enrich the response
        total_assets = (payload.residential_assets_value + 
                        payload.commercial_assets_value + 
                        payload.luxury_assets_value + 
                        payload.bank_asset_value)
        
        # Loan to Income Ratio
        lti_ratio = round((payload.loan_amount / payload.income_annum) * 100, 2) if payload.income_annum > 0 else 0
        # Asset Coverage Ratio (Total assets / loan amount)
        asset_cover = round(total_assets / payload.loan_amount, 2) if payload.loan_amount > 0 else 0
        
        return {
            "status": "success",
            "decision": decision,
            "probability": approval_probability,
            "lti_ratio": lti_ratio,
            "asset_cover": asset_cover,
            "cibil_status": "Excellent" if payload.cibil_score >= 750 else ("Good" if payload.cibil_score >= 650 else ("Average" if payload.cibil_score >= 550 else "Poor"))
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
