import argparse
import json
import time
import urllib.error
import urllib.request


def post_json(url: str, payload: dict, timeout_sec: float) -> tuple[int, dict, float]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            raw = response.read().decode("utf-8")
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            parsed = json.loads(raw)
            return response.status, parsed, elapsed_ms
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        try:
            err_payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            err_payload = {"error": str(exc)}
        return exc.code, err_payload, elapsed_ms


def normalize_risk(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().lower()
    if value in {"high risk", "high"}:
        return "high"
    if value in {"medium risk", "medium"}:
        return "medium"
    if value in {"low risk", "low"}:
        return "low"
    return value


def contract_check(response_json: dict, require_unit_score: bool) -> tuple[bool, str]:
    risk_raw = response_json.get("risk")
    score = response_json.get("score")

    if not isinstance(risk_raw, str):
        return False, "risk must be a string"
    risk = normalize_risk(risk_raw)
    if risk not in {"low", "medium", "high"}:
        return False, "risk must be low|medium|high"
    if not isinstance(score, (int, float)):
        return False, "score must be numeric"
    if require_unit_score and not (0.0 <= float(score) <= 1.0):
        return False, "score must be in 0..1"

    return True, "ok"


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay AI test cases against /predict endpoint")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/predict",
        help="Predict endpoint URL",
    )
    parser.add_argument(
        "--cases",
        default="data/manual_test_cases.json",
        help="Path to JSON test cases",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Request timeout in seconds",
    )
    parser.add_argument(
        "--require-unit-score",
        action="store_true",
        help="Require score to be in range 0..1",
    )
    args = parser.parse_args()

    with open(args.cases, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total = len(cases)
    success = 0
    matched = 0

    print(f"Running {total} test cases against {args.url}\n")

    for case in cases:
        case_id = case.get("id", "unknown-id")
        features = case.get("features", {})
        expected_risk = normalize_risk(case.get("expectedRisk", ""))

        status, response_json, elapsed_ms = post_json(args.url, features, args.timeout)
        got_risk = normalize_risk(response_json.get("risk", ""))
        got_score = response_json.get("score")

        is_ok, contract_reason = (False, "non-200 response")
        if status == 200:
            is_ok, contract_reason = contract_check(response_json, args.require_unit_score)
        is_match = expected_risk != "" and got_risk == expected_risk

        success += 1 if is_ok else 0
        matched += 1 if is_match else 0

        print(f"[{case_id}] status={status} latencyMs={elapsed_ms:.1f}")
        print(f"  expectedRisk={expected_risk or '-'} gotRisk={got_risk or '-'} score={got_score}")
        print(f"  contractOk={is_ok} reason={contract_reason} expectedMatch={is_match}")

    print("\nSummary")
    print(f"  total={total}")
    print(f"  contract_ok={success}/{total}")
    print(f"  expected_risk_match={matched}/{total}")


if __name__ == "__main__":
    main()
