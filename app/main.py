from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np

with open("data/global_iforest_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("data/global_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

app = FastAPI(title="Microshield AI Engine")

class RequestFeatures(BaseModel):
    pathLength: int
    bodySize: int
    queryParams: int
    specialChars: int
    entropy: float
    methodPOST: int

def calculate_risk(score: float) -> str:
    if score < -0.05:
        return "High Risk"
    elif score < -0.02:
        return "Medium Risk"
    else:
        return "Low Risk"
    
@app.post("/predict")
def predict(features: RequestFeatures):
    x =  np.array([[
        features.pathLength,
        features.bodySize,
        features.queryParams,
        features.specialChars,
        features.entropy,
        features.methodPOST
    ]])
    x_scaled = scaler.transform(x)

    score = model.decision_function(x_scaled)[0]

    risk = calculate_risk(score)
    return {
        "score": round(score, 4),
        "risk": risk
    }
