import pickle
import numpy as np

with open("data/global_iforest_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("data/global_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)    

FEATURE_ORDER = [
        "pathLength",
    "bodySize",
    "queryParams",
    "specialChars",
    "entropy",
    "methodPOST"
]

normal_sample = np.array([[12 , 150 , 1 , 3 , 3, 1]])
normal_scaled = scaler.transform(normal_sample)
normal_pred = model.predict(normal_scaled)
print(f"Normal sample prediction (1=normal, -1=anomaly): {normal_pred}")

attack_sample = np.array([[80, 6000, 10,40, 6.5, 1]])
attack_scaled = scaler.transform(attack_sample)
attack_pred = model.predict(attack_scaled)
print(f"Attack sample prediction (1=normal, -1=anomaly): {attack_pred}")