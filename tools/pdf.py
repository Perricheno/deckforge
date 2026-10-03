#!/usr/bin/env python3
"""Render decks to PDF (1280x720 pages) with headless Chromium.
  .venv/bin/python tools/pdf.py <slug|all> [--port 8191]
Needs the server running (it serves dist/). Output: decks/<slug>/<pdf name>; the server copies it into dist on the next build."""
import argparse, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("slug"); ap.add_argument("--port", type=int, default=8191)
a = ap.parse_args()
slugs = sorted(d.name for d in (ROOT / "decks").iterdir() if (d / "deck.json").exists()) if a.slug == "all" else [a.slug]
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for slug in slugs:
        deck = json.loads((ROOT / "decks" / slug / "deck.json").read_text())
        out = ROOT / "decks" / slug / (deck.get("pdf") or f"{slug}.pdf")
        pg = b.new_page(viewport={"width": 1440, "height": 810})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"http://127.0.0.1:{a.port}/{slug}/?pdf", wait_until="load")
        try:
            pg.wait_for_function("window.__ready===true", timeout=15000)
        except Exception:
            errs.append("deck never became ready")
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1500)
        pg.emulate_media(media="print")
        pg.pdf(path=str(out), width="1280px", height="720px", print_background=True, prefer_css_page_size=True)
        pg.close()
        print(f"{slug}: {out.relative_to(ROOT)}" + (f"  ERRORS: {errs}" if errs else ""))
        bad += bool(errs)
    b.close()
sys.exit(1 if bad else 0)
