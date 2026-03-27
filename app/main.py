from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import math
import numpy as np
import os

# Load models from parent directory's data folder
model_dir = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(model_dir, "global_iforest_model.pkl"), "rb") as f:
    model = pickle.load(f)

with open(os.path.join(model_dir, "global_scaler.pkl"), "rb") as f:
    scaler = pickle.load(f)

app = FastAPI(title="Microshield AI Engine")

class RequestFeatures(BaseModel):
    pathLength: int
    bodySize: int
    queryParams: int
    specialChars: int
    entropy: float
    methodPOST: int
    ipReqPerMin: float = 0.0
    routeReqPerMin: float = 0.0
    uniquePathsPerMin: float = 0.0
    postRatioPerMin: float = 0.0

def normalize_model_score(raw_score: float) -> float:
    # IsolationForest decision_function: lower values are more anomalous.
    # Sigmoid on negative raw score maps risk into a stable 0..1 range.
    return 1.0 / (1.0 + math.exp(8.0 * raw_score))

def behavior_pressure(features: RequestFeatures) -> float:
    ip_pressure = min(1.0, float(features.ipReqPerMin) / 120.0)
    route_pressure = min(1.0, float(features.routeReqPerMin) / 80.0)
    path_pressure = min(1.0, float(features.uniquePathsPerMin) / 40.0)
    post_pressure = min(1.0, max(0.0, float(features.postRatioPerMin)))

    return min(
        1.0,
        (0.45 * ip_pressure)
        + (0.25 * route_pressure)
        + (0.20 * path_pressure)
        + (0.10 * post_pressure),
    )


def content_anomaly_boost(features: RequestFeatures) -> float:
    boost = 0.0

    # These are escalation heuristics for extreme payload characteristics
    # that often show up in automated attack traffic.
    if features.specialChars >= 60:
        boost += 0.07
    if features.entropy >= 6.0:
        boost += 0.05
    if features.bodySize >= 5000:
        boost += 0.05
    if features.queryParams >= 10:
        boost += 0.03
    if features.pathLength >= 100:
        boost += 0.03

    return min(0.20, boost)


def is_extreme_payload(features: RequestFeatures) -> bool:
    extreme_entropy = features.entropy >= 7.0 and features.specialChars >= 80
    extreme_size = features.bodySize >= 7000 and features.pathLength >= 100
    extreme_mix = features.queryParams >= 14 and features.specialChars >= 70
    return extreme_entropy or extreme_size or extreme_mix

def calculate_risk(score_0_to_1: float) -> str:
    if score_0_to_1 >= 0.70:
        return "high"
    if score_0_to_1 >= 0.44:
        return "medium"
    return "low"


def build_reason(features: RequestFeatures, model_score: float, pressure: float, content_boost: float, score: float, risk: str) -> str:
    reasons = [
        f"Base anomaly score={model_score:.3f}",
        f"Behavior pressure={pressure:.3f}",
        f"Content boost={content_boost:.3f}",
        f"Final score={score:.3f} ({risk})",
    ]

    flags = []
    if features.specialChars >= 60:
        flags.append("high special character density")
    if features.entropy >= 6.0:
        flags.append("high payload entropy")
    if features.bodySize >= 5000:
        flags.append("large body size")
    if features.queryParams >= 10:
        flags.append("many query parameters")
    if features.pathLength >= 100:
        flags.append("long path")
    if features.ipReqPerMin >= 90:
        flags.append("high request rate from IP")

    if flags:
        reasons.append("Signals: " + ", ".join(flags))

    return " | ".join(reasons)
    
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

    raw_score = float(model.decision_function(x_scaled)[0])
    model_score = normalize_model_score(raw_score)
    pressure = behavior_pressure(features)
    content_boost = content_anomaly_boost(features)
    score = min(1.0, max(0.0, (0.72 * model_score) + (0.20 * pressure) + (0.25 * content_boost)))

    risk = calculate_risk(score)
    if risk == "medium" and is_extreme_payload(features) and score >= 0.60:
        risk = "high"

    reason = build_reason(features, model_score, pressure, content_boost, score, risk)

    return {
        "score": round(score, 4),
        "risk": risk,
        "reason": reason,
        "signals": {
            "modelScore": round(model_score, 4),
            "behaviorPressure": round(pressure, 4),
            "contentBoost": round(content_boost, 4),
        },
    }
