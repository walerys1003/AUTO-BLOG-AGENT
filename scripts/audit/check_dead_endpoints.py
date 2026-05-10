#!/usr/bin/env python3
"""
FAZA 2.2 — Detektor martwych endpointów.

Endpoint w app.url_map jest "martwy" jeśli:
- nie pojawia się w żadnym url_for(...) w templates/
- jego ścieżka URL nie jest hardcoded w żadnym fetch()/axios w static/js/
- jego ścieżka URL nie jest hardcoded w form action="" w templates/

Dla endpointów /api/* z metodą non-GET ostrzegamy oddzielnie (kandydaci do
sprawdzenia ręcznego — często wołane przez AJAX).

Użycie:
    python3 scripts/audit/check_dead_endpoints.py
    python3 scripts/audit/check_dead_endpoints.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "templates"
STATIC_JS_DIR = ROOT / "static" / "js"

URL_FOR_RE = re.compile(r"""url_for\(\s*['"]([A-Za-z_][A-Za-z0-9_.]*)['"]""")
# fetch('/foo'), fetch("/foo"), fetch(`/foo/${x}`)
HARDCODED_PATH_RE = re.compile(r"""['"`](/[A-Za-z0-9_\-/.]+)""")


def collect_text(paths: list[Path]) -> str:
    out: list[str] = []
    for p in paths:
        try:
            out.append(p.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            out.append(p.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(out)


def url_for_endpoints() -> set[str]:
    used: set[str] = set()
    for path in TEMPLATES_DIR.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        used.update(URL_FOR_RE.findall(text))
    return used


def hardcoded_paths() -> set[str]:
    """Set of literal path strings appearing in templates and JS."""
    paths: set[str] = set()
    sources: list[Path] = []
    if TEMPLATES_DIR.exists():
        sources.extend(TEMPLATES_DIR.rglob("*.html"))
    if STATIC_JS_DIR.exists():
        sources.extend(STATIC_JS_DIR.rglob("*.js"))
    blob = collect_text(sources)
    for m in HARDCODED_PATH_RE.findall(blob):
        # strip parameter slots like /foo/${id} -> /foo/
        paths.add(m)
    return paths


def rule_path_matches_hardcoded(rule_path: str, hardcoded: set[str]) -> bool:
    """
    Checks whether a rule path like '/api/blogs/<int:blog_id>/categories'
    matches any hardcoded path like '/api/blogs/' or '/api/blogs/${id}/categories'.
    Strategy: strip <...> placeholders from rule_path, then test prefix/contains.
    """
    # turn /api/blogs/<int:blog_id>/categories -> /api/blogs/  + /categories
    static_parts = re.split(r"<[^>]+>", rule_path)
    static_parts = [p for p in static_parts if p and p != "/"]
    if not static_parts:
        return False
    # The biggest static prefix
    prefix = static_parts[0].rstrip("/")
    if not prefix:
        return False
    for hp in hardcoded:
        if hp.startswith(prefix):
            return True
    return False


def load_app():
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("USE_MOCK_ADAPTER", "1")
    from app import app  # noqa: WPS433
    return app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    app = load_app()
    used = url_for_endpoints()
    hardcoded = hardcoded_paths()

    rules = list(app.url_map.iter_rules())

    truly_dead: list[dict] = []
    likely_ajax: list[dict] = []
    static_handled: list[str] = []

    for rule in rules:
        ep = rule.endpoint
        if ep == "static":
            continue
        if ep in used:
            continue
        # ignore endpoints belonging to debug toolbar, etc.
        if ep.startswith(("debugtoolbar.", "_debug_toolbar.")):
            continue

        rule_path = str(rule.rule)
        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
        info = {
            "endpoint": ep,
            "path": rule_path,
            "methods": methods,
        }

        if rule_path_matches_hardcoded(rule_path, hardcoded):
            likely_ajax.append(info)
        elif rule_path.startswith("/api/") or "POST" in methods:
            likely_ajax.append(info)
        else:
            truly_dead.append(info)

    if args.json:
        print(json.dumps({
            "truly_dead": truly_dead,
            "likely_ajax": likely_ajax,
            "static_handled": static_handled,
        }, indent=2, ensure_ascii=False))
        return 0

    print("=" * 70)
    print("FAZA 2.2  Dead endpoint detector")
    print("=" * 70)
    print(f"Total endpoints       : {len(rules)}")
    print(f"Used via url_for()    : {len(used)}")
    print(f"Truly dead candidates : {len(truly_dead)}")
    print(f"Likely AJAX (review)  : {len(likely_ajax)}")
    print()

    if truly_dead:
        print("PRAWDOPODOBNIE MARTWE (do usunięcia / sprawdzenia):")
        print("-" * 70)
        for info in sorted(truly_dead, key=lambda x: x["endpoint"]):
            methods = ",".join(info["methods"])
            print(f"  {info['endpoint']:50s}  [{methods}]  {info['path']}")
        print()

    if likely_ajax:
        print(f"AJAX/API kandydaci (zostawiamy, raczej OK) — {len(likely_ajax)}:")
        print("-" * 70)
        for info in sorted(likely_ajax, key=lambda x: x["endpoint"])[:25]:
            methods = ",".join(info["methods"])
            print(f"  {info['endpoint']:50s}  [{methods}]  {info['path']}")
        if len(likely_ajax) > 25:
            print(f"  ... i {len(likely_ajax) - 25} więcej (użyj --json by zobaczyć wszystkie)")

    print()
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
