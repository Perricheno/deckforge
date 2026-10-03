#!/usr/bin/env python3
"""Screenshot slides of a deck (animated mode) to check layout: prints the PNG paths.
  .venv/bin/python tools/shot.py <slug> [--slide N] [--mobile] [--wait 2.4] [--port 8191]
Look at the images (Read tool) before telling the user a deck is done."""
import argparse, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("slug"); ap.add_argument("--slide", type=int, default=0)
ap.add_argument("--mobile", action="store_true"); ap.add_argument("--wait", type=float, default=2.4); ap.add_argument("--port", type=int, default=8191)
a = ap.parse_args()
out = Path(tempfile.gettempdir()) / "deckforge-shots"; out.mkdir(exist_ok=True)
vp = {"width": 390, "height": 844} if a.mobile else {"width": 1440, "height": 810}
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport=vp, device_scale_factor=2 if a.mobile else 1, is_mobile=a.mobile, has_touch=a.mobile)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(f"http://127.0.0.1:{a.port}/{a.slug}/", wait_until="load")
    pg.wait_for_function("window.__ready===true", timeout=15000)
    n = pg.evaluate("window.__deckCount ? window.__deckCount() : document.querySelectorAll('.slide').length")
    for k in range(n):
        if a.slide and k + 1 != a.slide:
            pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300); continue
        pg.wait_for_timeout(int(a.wait * 1000))
        f = out / f"{a.slug}-{k+1}.png"; pg.screenshot(path=str(f)); print(f)
        pg.keyboard.press("ArrowRight")
    print("console errors:", errs or "none"); b.close()
