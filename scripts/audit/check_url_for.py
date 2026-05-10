#!/usr/bin/env python3
"""
FAZA 2.1 — Walidator url_for() vs app.url_map.

Skanuje wszystkie pliki w templates/ i wyciąga wywołania url_for(...).
Następnie ładuje aplikację Flask i porównuje każdy endpoint z app.url_map.

Wynik:
- Lista WSZYSTKICH użyć url_for w szablonach (plik:linia -> endpoint)
- Lista BROKEN (endpoint nie istnieje w url_map)
- Lista DEAD (endpointy w url_map nieużywane w żadnym szablonie - poglądowo)
- Exit code 1 jeśli znaleziono broken refs

Użycie:
    python3 scripts/audit/check_url_for.py
    python3 scripts/audit/check_url_for.py --json   # output JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "templates"

# url_for('endpoint', ...) lub url_for("endpoint", ...)
URL_FOR_RE = re.compile(
    r"""url_for\(\s*['"]([A-Za-z_][A-Za-z0-9_.]*)['"]""",
    re.MULTILINE,
)


def find_url_for_calls() -> list[tuple[str, int, str]]:
    """Returns list of (relative_path, line_no, endpoint)."""
    calls: list[tuple[str, int, str]] = []
    if not TEMPLATES_DIR.exists():
        print(f"ERROR: {TEMPLATES_DIR} not found", file=sys.stderr)
        return calls

    for path in TEMPLATES_DIR.rglob("*.html"):
        rel = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")

        for m in URL_FOR_RE.finditer(text):
            endpoint = m.group(1)
            # compute line number
            line_no = text.count("\n", 0, m.start()) + 1
            calls.append((str(rel), line_no, endpoint))
    return calls


def load_app_endpoints() -> set[str]:
    """Import the app and return set of all endpoint names."""
    sys.path.insert(0, str(ROOT))
    # Avoid the scheduler / external services starting up
    os.environ.setdefault("USE_MOCK_ADAPTER", "1")
    try:
        from app import app  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: cannot import Flask app: {exc}", file=sys.stderr)
        raise
    return {rule.endpoint for rule in app.url_map.iter_rules()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--show-dead",
        action="store_true",
        help="Also list endpoints defined in app.url_map but never referenced via url_for",
    )
    args = parser.parse_args()

    calls = find_url_for_calls()
    endpoints = load_app_endpoints()

    used_endpoints: set[str] = set()
    broken: list[tuple[str, int, str]] = []
    by_endpoint: dict[str, list[tuple[str, int]]] = defaultdict(list)

    for rel, line_no, endpoint in calls:
        used_endpoints.add(endpoint)
        by_endpoint[endpoint].append((rel, line_no))
        if endpoint not in endpoints:
            broken.append((rel, line_no, endpoint))

    dead = sorted(endpoints - used_endpoints)

    if args.json:
        print(json.dumps({
            "total_calls": len(calls),
            "unique_endpoints_used": len(used_endpoints),
            "total_endpoints_defined": len(endpoints),
            "broken": [
                {"file": f, "line": ln, "endpoint": ep}
                for f, ln, ep in broken
            ],
            "dead_endpoints": dead if args.show_dead else None,
            "by_endpoint": {
                ep: [{"file": f, "line": ln} for f, ln in locs]
                for ep, locs in by_endpoint.items()
            },
        }, indent=2, ensure_ascii=False))
        return 1 if broken else 0

    # Human-readable
    print("=" * 70)
    print("FAZA 2.1  url_for() validation report")
    print("=" * 70)
    print(f"Templates scanned   : {len(list(TEMPLATES_DIR.rglob('*.html')))}")
    print(f"url_for() calls     : {len(calls)}")
    print(f"Unique endpoints    : {len(used_endpoints)}")
    print(f"App.url_map endpoints: {len(endpoints)}")
    print()

    if broken:
        print(f"BROKEN url_for() — endpoint nie istnieje ({len(broken)}):")
        print("-" * 70)
        # group by endpoint for readability
        broken_by_ep: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for f, ln, ep in broken:
            broken_by_ep[ep].append((f, ln))
        for ep in sorted(broken_by_ep):
            locs = broken_by_ep[ep]
            print(f"  {ep!r}  ({len(locs)} użyć)")
            for f, ln in locs:
                print(f"      - {f}:{ln}")
    else:
        print("OK — wszystkie url_for() trafiają w istniejące endpointy.")

    if args.show_dead and dead:
        print()
        print(f"NIEUŻYWANE endpointy ({len(dead)}) — istnieją w url_map, brak url_for():")
        print("-" * 70)
        for ep in dead:
            print(f"  - {ep}")

    print()
    print("=" * 70)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
