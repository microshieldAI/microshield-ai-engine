import argparse
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional, Tuple


def post_json(
    url: str,
    payload: Dict[str, Any],
    timeout_sec: float,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Dict[str, Any], Dict[str, str], float, str]:
    method = (method or "POST").upper()
    req_headers = {"Content-Type": "application/json"}
    if isinstance(headers, dict):
        req_headers.update({str(k): str(v) for k, v in headers.items()})

    body = None
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        body = json.dumps(payload or {}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=req_headers,
        method=method,
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            raw_text = response.read().decode("utf-8")
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            headers = {k: v for k, v in response.headers.items()}
            try:
                parsed = json.loads(raw_text)
            except Exception:
                parsed = {"raw": raw_text}
            return response.status, parsed, headers, elapsed_ms, ""
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        err_raw = exc.read().decode("utf-8")
        headers = {k: v for k, v in exc.headers.items()}
        try:
            parsed = json.loads(err_raw)
        except Exception:
            parsed = {"raw": err_raw}
        return exc.code, parsed, headers, elapsed_ms, ""
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return 0, {}, {}, elapsed_ms, str(exc)


def normalize_risk(risk_value: Any) -> str:
    if not isinstance(risk_value, str):
        return ""
    v = risk_value.strip().lower()
    if v in {"high", "high risk"}:
        return "high"
    if v in {"medium", "medium risk"}:
        return "medium"
    if v in {"low", "low risk"}:
        return "low"
    return v


def ai_contract_ok(result: Dict[str, Any], require_unit_score: bool) -> Tuple[bool, str]:
    score = result.get("score")
    risk = normalize_risk(result.get("risk"))

    if not isinstance(score, (int, float)):
        return False, "score is missing or not numeric"
    if require_unit_score and not (0.0 <= float(score) <= 1.0):
        return False, "score is not in 0..1"
    if risk not in {"low", "medium", "high"}:
        return False, "risk is not low|medium|high"
    return True, "ok"


def source_from_response(headers: Dict[str, str], body: Dict[str, Any]) -> str:
    header_val = headers.get("X-Microshield-Source") or headers.get("x-microshield-source")
    if isinstance(header_val, str) and header_val.strip():
        return header_val.strip()
    body_source = body.get("source")
    if isinstance(body_source, str) and body_source.strip():
        return body_source.strip()
    return "UNKNOWN"


def infer_source(status: int, source: str) -> str:
    if source == "UNKNOWN" and status == 429:
        return "RATE_LIMIT"
    return source


def case_category(case: Dict[str, Any]) -> str:
    explicit = case.get("category")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()
    case_id = str(case.get("id", "uncategorized"))
    return case_id.split("-")[0].lower() if case_id else "uncategorized"


def default_ai_cases() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ai-benign",
            "payload": {
                "pathLength": 10,
                "bodySize": 120,
                "queryParams": 1,
                "specialChars": 1,
                "entropy": 1.3,
                "methodPOST": 0,
            },
            "expectedRisk": "low",
        },
        {
            "id": "ai-suspicious",
            "payload": {
                "pathLength": 25,
                "bodySize": 700,
                "queryParams": 3,
                "specialChars": 8,
                "entropy": 3.8,
                "methodPOST": 1,
            },
            "expectedRisk": "medium",
        },
        {
            "id": "ai-attack",
            "payload": {
                "pathLength": 80,
                "bodySize": 6000,
                "queryParams": 10,
                "specialChars": 40,
                "entropy": 6.5,
                "methodPOST": 1,
            },
            "expectedRisk": "high",
        },
    ]


def default_middleware_cases() -> List[Dict[str, Any]]:
    return [
        {
            "id": "mw-static-sqli",
            "payload": {
                "username": "admin' OR 1=1 --",
                "password": "x",
            },
            "expectedSource": "STATIC_RULE",
            "expectedBlocked": True,
        },
        {
            "id": "mw-static-xss",
            "payload": {
                "comment": "<script>alert('xss')</script>",
            },
            "expectedSource": "STATIC_RULE",
            "expectedBlocked": True,
        },
        {
            "id": "mw-ai-path",
            "payload": {
                "message": "normal payload without obvious static attack",
                "filler": "A" * 300,
            },
            "expectedSource": "AI_ENGINE",
            "expectedBlocked": None,
        },
    ]


def load_cases_from_file(path: Optional[str], fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not path:
        return fallback
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Cases file must contain a JSON array: {path}")
    return data


def source_matches_expected(actual_source: str, expected_source: Any) -> bool:
    if expected_source is None:
        return True
    if isinstance(expected_source, str):
        return actual_source == expected_source
    if isinstance(expected_source, list):
        normalized = [s for s in expected_source if isinstance(s, str)]
        return actual_source in normalized
    return False


def build_case_url(base_url: str, path: str) -> str:
    if not path:
        return base_url
    normalized_base = base_url if base_url.endswith("/") else base_url + "/"
    normalized_path = path[1:] if path.startswith("/") else path
    return urljoin(normalized_base, normalized_path)


def run_ai_tests(ai_url: str, timeout_sec: float, require_unit_score: bool, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    result_rows = []
    contract_ok_count = 0
    expected_match_count = 0

    for case in cases:
        status, body, _, latency_ms, error = post_json(ai_url, case["payload"], timeout_sec)
        risk = normalize_risk(body.get("risk"))
        score = body.get("score")

        if status == 200 and not error:
            contract_ok, reason = ai_contract_ok(body, require_unit_score)
        else:
            contract_ok, reason = False, error or f"HTTP {status}"

        expected = normalize_risk(case.get("expectedRisk"))
        expected_match = expected != "" and expected == risk

        if contract_ok:
            contract_ok_count += 1
        if expected_match:
            expected_match_count += 1

        result_rows.append(
            {
                "id": case["id"],
                "status": status,
                "latencyMs": round(latency_ms, 1),
                "score": score,
                "risk": risk,
                "expectedRisk": expected,
                "expectedMatch": expected_match,
                "contractOk": contract_ok,
                "reason": reason,
            }
        )

    return {
        "total": len(cases),
        "contractOk": contract_ok_count,
        "expectedRiskMatch": expected_match_count,
        "rows": result_rows,
    }


def run_middleware_tests(middleware_url: str, timeout_sec: float, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    source_counts: Dict[str, int] = {}
    source_match_count = 0
    blocked_match_count = 0
    category_stats: Dict[str, Dict[str, Any]] = {}

    for case in cases:
        method = str(case.get("method", "POST")).upper()
        path = str(case.get("path", ""))
        headers_cfg = case.get("headers") if isinstance(case.get("headers"), dict) else {}
        repeats = max(1, int(case.get("repeat", 1)))
        case_url = build_case_url(middleware_url, path)

        attempts = []
        blocked_attempts = 0

        for _ in range(repeats):
            status, body, headers, latency_ms, error = post_json(
                case_url,
                case.get("payload", {}),
                timeout_sec,
                method=method,
                headers=headers_cfg,
            )
            source = source_from_response(headers, body)
            blocked = status >= 400
            if blocked:
                blocked_attempts += 1
            attempts.append((status, body, headers, latency_ms, error, source, blocked))

        status, body, headers, latency_ms, error, source, blocked = attempts[-1]
        source = infer_source(status, source)

        source_counts[source] = source_counts.get(source, 0) + 1

        expected_source = case.get("expectedSource")
        expected_blocked = case.get("expectedBlocked")

        source_match = source_matches_expected(source, expected_source)
        blocked_match = (expected_blocked is None) or (blocked == expected_blocked)

        if source_match:
            source_match_count += 1
        if blocked_match:
            blocked_match_count += 1

        category = case_category(case)
        if category not in category_stats:
            category_stats[category] = {
                "total": 0,
                "blocked": 0,
                "sourceMatch": 0,
                "blockedMatch": 0,
                "sources": {},
            }
        c = category_stats[category]
        c["total"] += 1
        c["blocked"] += 1 if blocked else 0
        c["sourceMatch"] += 1 if source_match else 0
        c["blockedMatch"] += 1 if blocked_match else 0
        c["sources"][source] = c["sources"].get(source, 0) + 1

        rows.append(
            {
                "id": case["id"],
                "category": category,
                "method": method,
                "path": path or "/",
                "repeats": repeats,
                "blockedAttempts": blocked_attempts,
                "status": status,
                "latencyMs": round(latency_ms, 1),
                "blocked": blocked,
                "source": source,
                "expectedSource": expected_source,
                "sourceMatch": source_match,
                "expectedBlocked": expected_blocked,
                "blockedMatch": blocked_match,
                "error": error,
                "body": body,
            }
        )

    return {
        "total": len(cases),
        "sourceCounts": source_counts,
        "sourceMatch": source_match_count,
        "blockedMatch": blocked_match_count,
        "categoryStats": category_stats,
        "rows": rows,
    }


def print_ai_report(report: Dict[str, Any]) -> None:
    print("\nAI TEST REPORT")
    print(f"total={report['total']} contractOk={report['contractOk']} expectedRiskMatch={report['expectedRiskMatch']}")
    for row in report["rows"]:
        print(
            f"[{row['id']}] status={row['status']} latencyMs={row['latencyMs']} "
            f"risk={row['risk']} expected={row['expectedRisk']} score={row['score']} "
            f"contractOk={row['contractOk']} match={row['expectedMatch']} reason={row['reason']}"
        )


def print_middleware_report(report: Dict[str, Any]) -> None:
    print("\nMIDDLEWARE TEST REPORT")
    print(
        f"total={report['total']} sourceMatch={report['sourceMatch']} "
        f"blockedMatch={report['blockedMatch']} sourceCounts={report['sourceCounts']}"
    )
    for row in report["rows"]:
        print(
            f"[{row['id']}] category={row['category']} {row['method']} {row['path']} repeats={row['repeats']} "
            f"blockedAttempts={row['blockedAttempts']} status={row['status']} latencyMs={row['latencyMs']} "
            f"blocked={row['blocked']} source={row['source']} "
            f"expectedSource={row['expectedSource']} sourceMatch={row['sourceMatch']} "
            f"expectedBlocked={row['expectedBlocked']} blockedMatch={row['blockedMatch']}"
        )

    print("\nCATEGORY SUMMARY")
    for category in sorted(report.get("categoryStats", {}).keys()):
        c = report["categoryStats"][category]
        print(
            f"[{category}] total={c['total']} blocked={c['blocked']} "
            f"sourceMatch={c['sourceMatch']} blockedMatch={c['blockedMatch']} sources={c['sources']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Full tester for AI endpoint and MicroShield middleware")
    parser.add_argument("--mode", choices=["ai", "middleware", "both"], default="both")
    parser.add_argument("--ai-url", default="http://127.0.0.1:8000/predict")
    parser.add_argument("--middleware-url", default="http://127.0.0.1:3000/")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--require-unit-score", action="store_true")
    parser.add_argument("--ai-cases", default="")
    parser.add_argument("--middleware-cases", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    full_report: Dict[str, Any] = {"mode": args.mode}

    if args.mode in {"ai", "both"}:
        ai_cases = load_cases_from_file(args.ai_cases or None, default_ai_cases())
        ai_report = run_ai_tests(args.ai_url, args.timeout, args.require_unit_score, ai_cases)
        full_report["ai"] = ai_report
        print_ai_report(ai_report)

    if args.mode in {"middleware", "both"}:
        mw_cases = load_cases_from_file(args.middleware_cases or None, default_middleware_cases())
        mw_report = run_middleware_tests(args.middleware_url, args.timeout, mw_cases)
        full_report["middleware"] = mw_report
        print_middleware_report(mw_report)

    print("\nJSON SUMMARY")
    print(json.dumps(full_report, indent=2))

    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2)
        print(f"\nSaved report to {args.output}")


if __name__ == "__main__":
    main()
