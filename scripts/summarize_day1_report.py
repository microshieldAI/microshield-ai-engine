import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate compact Day 1 markdown summary")
    parser.add_argument("--input", required=True, help="Path to full tester JSON report")
    parser.add_argument("--output", required=True, help="Path to markdown summary output")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        report = json.load(f)

    input_name = Path(args.input).name.lower()
    if "day2" in input_name:
        title = "# Day 2 Middleware Benchmark Summary"
    elif "day3" in input_name:
        title = "# Day 3 Middleware Benchmark Summary"
    else:
        title = "# Day 1 Middleware Benchmark Summary"

    mw = report.get("middleware", {})
    rows = mw.get("rows", [])
    total = int(mw.get("total", 0))
    source_match = int(mw.get("sourceMatch", 0))
    blocked_match = int(mw.get("blockedMatch", 0))
    source_counts = mw.get("sourceCounts", {})
    category_stats = mw.get("categoryStats", {})

    mismatches = [
        r for r in rows if (not r.get("sourceMatch", True)) or (not r.get("blockedMatch", True))
    ]

    mismatch_by_category = Counter(r.get("category", "uncategorized") for r in mismatches)

    lines = []
    lines.append(title)
    lines.append("")
    lines.append("## Overall")
    lines.append(f"- Total cases: {total}")
    lines.append(f"- Source match: {source_match}/{total}")
    lines.append(f"- Blocked match: {blocked_match}/{total}")
    lines.append(f"- Source distribution: {source_counts}")
    lines.append("")

    lines.append("## Category Summary")
    for category in sorted(category_stats.keys()):
        c = category_stats[category]
        lines.append(
            f"- {category}: total={c.get('total', 0)}, blocked={c.get('blocked', 0)}, "
            f"sourceMatch={c.get('sourceMatch', 0)}, blockedMatch={c.get('blockedMatch', 0)}, "
            f"sources={c.get('sources', {})}"
        )
    lines.append("")

    lines.append("## Top Gaps")
    if not mismatches:
        lines.append("- No mismatches detected.")
    else:
        for category, count in mismatch_by_category.most_common(10):
            lines.append(f"- {category}: {count} mismatch cases")

    lines.append("")
    lines.append("## Next Actions")
    lines.append("- Tune expectedSource for benchmark cases affected by RATE_LIMIT if limiter is intentionally active.")
    lines.append("- Tune AI thresholds to raise risk on suspicious/attack payload categories still marked low.")
    lines.append("- Add explicit test routes for scanner paths in test app for cleaner source attribution when needed.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
