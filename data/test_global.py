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

normal_sample = np.array([[30, 450, 2, 6, 2.8, 1]

])
normal_scaled = scaler.transform(normal_sample)
normal_pred = model.predict(normal_scaled)
print(f"Normal sample prediction (1=normal, -1=anomaly): {normal_pred}")

attack_sample = np.array([[45, 2500, 6, 30, 5.5, 1]



])
attack_scaled = scaler.transform(attack_sample)
attack_pred = model.predict(attack_scaled)
print(f"Attack sample prediction (1=normal, -1=anomaly): {attack_pred}")
score_normal = model.decision_function(normal_scaled)[0]
score_attack = model.decision_function(attack_scaled)[0]

print("Normal score:", score_normal)
print("Attack score:", score_attack)
