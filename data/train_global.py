import json
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ==============================
# CONFIGURATION
# ==============================

DATASET_PATH = "data/global_data_set.json"
MODEL_PATH = "data/global_iforest_model.pkl"
SCALER_PATH = "data/global_scaler.pkl"

FEATURE_ORDER = [
    "pathLength",
    "bodySize",
    "queryParams",
    "specialChars",
    "entropy",
    "methodPOST"
]

N_ESTIMATORS = 200
CONTAMINATION = 0.02
RANDOM_STATE = 42

# ==============================
# 1. LOAD DATASET
# ==============================

with open(DATASET_PATH, "r") as f:
    data = json.load(f)

if len(data) == 0:
    raise ValueError("Dataset is empty. Cannot train model.")

# ==============================
# 2. CONVERT JSON → NUMERIC MATRIX
# ==============================

X = []
for sample in data:
    try:
        row = [sample[feature] for feature in FEATURE_ORDER]
        X.append(row)
    except KeyError as e:
        raise KeyError(f"Missing feature in dataset: {e}")

X = np.array(X)

print(f"Loaded dataset with shape: {X.shape}")

# ==============================
# 3. FEATURE SCALING
# ==============================

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Feature scaling completed.")

# ==============================
# 4. TRAIN ISOLATION FOREST
# ==============================

model = IsolationForest(
    n_estimators=N_ESTIMATORS,
    contamination=CONTAMINATION,
    random_state=RANDOM_STATE,
    n_jobs=-1
)

model.fit(X_scaled)

print("Isolation Forest training completed.")

# ==============================
# 5. SAVE MODEL & SCALER
# ==============================

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

with open(SCALER_PATH, "wb") as f:
    pickle.dump(scaler, f)

print("Model saved to:", MODEL_PATH)
print("Scaler saved to:", SCALER_PATH)

# ==============================
# 6. QUICK SANITY CHECK (OPTIONAL)
# ==============================

sample_normal = np.array([[12, 150, 1, 2, 1.2, 1]])
sample_attack = np.array([[45, 2500, 6, 30, 5.5, 1]])

sample_normal_scaled = scaler.transform(sample_normal)
sample_attack_scaled = scaler.transform(sample_attack)

normal_score = model.decision_function(sample_normal_scaled)[0]
attack_score = model.decision_function(sample_attack_scaled)[0]

print("\nSanity Check Scores:")
print(f"Normal sample score  : {normal_score:.4f}")
print(f"Attack sample score  : {attack_score:.4f}")

print("\n✅ Global model training finished successfully.")
