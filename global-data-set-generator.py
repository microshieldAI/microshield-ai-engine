import json
import math
import random

# Shannon entropy
def calculate_entropy(text):
    if not text:
        return 0
    probabilities = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probabilities)

# Common human words seen in normal requests
WORDS = [
    "login", "user", "email", "password", "data", "value",
    "profile", "update", "submit", "form", "request",
    "hello", "name", "message", "comment"
]

data = []

for _ in range(5000):
    path_len = random.randint(5, 30)
    body_size = random.randint(50, 400)
    query_params = random.randint(0, 3)
    special_chars = random.randint(0, 5)

    # Generate human-like structured body
    words_count = body_size // 6
    body_text = " ".join(random.choices(WORDS, k=words_count))

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

with open("data/global_data_set.json", "w") as f:
    json.dump(data, f, indent=4)

print("✅ Global dataset generated (human-like normal traffic)")
