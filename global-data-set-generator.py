import json 
import math
import random

def calculate_entropy(text):
    probability = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    entropy = - sum([p * math.log2(p) for p in probability])
    return entropy

data = []

for i in range(5000):
    path_len = random.randint(5,30)
    body_size = random.randint(20,500)
    special_chars = random.randint(0,8)
    query_params = random.randint(0,4)

    body_text = "a" * body_size + "!" * special_chars
    entropy = calculate_entropy(body_text)

    sample = {
        "pathLength": path_len,
        "bodySize": body_size,
        "queryParams": query_params,
        "specialChars": special_chars,
        "entropy": entropy,
        "methodPOST": random.choice([0, 1])
    }

    data.append(sample)

json.dump(data,open("data/global_data_set.json","w"),indent=4)