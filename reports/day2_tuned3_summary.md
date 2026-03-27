# Day 2 Middleware Benchmark Summary

## Overall
- Total cases: 54
- Source match: 49/54
- Blocked match: 48/54
- Source distribution: {'AI_ENGINE': 4, 'STATIC_RULE': 50}

## Category Summary
- benign: total=3, blocked=0, sourceMatch=3, blockedMatch=3, sources={'AI_ENGINE': 3}
- bot: total=2, blocked=2, sourceMatch=2, blockedMatch=2, sources={'STATIC_RULE': 2}
- cmd: total=3, blocked=3, sourceMatch=3, blockedMatch=3, sources={'STATIC_RULE': 3}
- command: total=1, blocked=1, sourceMatch=1, blockedMatch=1, sources={'STATIC_RULE': 1}
- encoded: total=2, blocked=2, sourceMatch=2, blockedMatch=2, sources={'STATIC_RULE': 2}
- json: total=1, blocked=0, sourceMatch=1, blockedMatch=0, sources={'AI_ENGINE': 1}
- mixed: total=5, blocked=5, sourceMatch=0, blockedMatch=0, sources={'STATIC_RULE': 5}
- path: total=3, blocked=3, sourceMatch=3, blockedMatch=3, sources={'STATIC_RULE': 3}
- recon: total=2, blocked=2, sourceMatch=2, blockedMatch=2, sources={'STATIC_RULE': 2}
- scanner: total=7, blocked=7, sourceMatch=7, blockedMatch=7, sources={'STATIC_RULE': 7}
- sqli: total=4, blocked=4, sourceMatch=4, blockedMatch=4, sources={'STATIC_RULE': 4}
- suspicious: total=3, blocked=3, sourceMatch=3, blockedMatch=3, sources={'STATIC_RULE': 3}
- ua: total=14, blocked=14, sourceMatch=14, blockedMatch=14, sources={'STATIC_RULE': 14}
- xss: total=4, blocked=4, sourceMatch=4, blockedMatch=4, sources={'STATIC_RULE': 4}

## Top Gaps
- mixed: 5 mismatch cases
- json: 1 mismatch cases

## Next Actions
- Tune expectedSource for benchmark cases affected by RATE_LIMIT if limiter is intentionally active.
- Tune AI thresholds to raise risk on suspicious/attack payload categories still marked low.
- Add explicit test routes for scanner paths in test app for cleaner source attribution when needed.
