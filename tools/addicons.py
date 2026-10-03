#!/usr/bin/env python3
"""Add Lucide icons to assets/vendor/icons.js:  python tools/addicons.py chart-pie map-pin ...
Names are the kebab-case ids from lucide.dev; the deck uses the camelCase export (chartPie, mapPin)."""
import re, sys, urllib.request
from pathlib import Path
F = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "icons.js"
src = F.read_text()
for name in sys.argv[1:]:
    var = re.sub(r"-(\w)", lambda m: m.group(1).upper(), name)
    if f"export const {var} " in src:
        print(f"{var}: already there"); continue
    try:
        js = urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/lucide@latest/dist/esm/icons/{name}.js", timeout=20).read().decode()
    except Exception as e:
        print(f"{name}: not found ({e})"); continue
    m = re.search(r"const \w+ = (\[.*\]);\s*export", js, re.S)
    src += f"export const {var} = {m.group(1)};\n"; print(f"{name} -> {var}")
F.write_text(src)
