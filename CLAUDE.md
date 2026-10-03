# deckforge

Presentations as data. `decks/<slug>/deck.json` -> engine builds a site with looped motion graphics, PDF export, a phone remote (PIN + SSE) and a gallery. Live at https://x.perricheno.com (service `deckforge`, port 8191, Cloudflare tunnel; nothing is cached).

- Make or change a deck: skill `deck-build` (content only, never HTML). Speaker text: skill `deck-speech`.
- Layout: `engine/` (theme css, motion.js, remote.js, gallery.html, admin.html), `tools/` (build.py, serve.py, pdf.py, shot.py, addicons.py, setpin.py), `assets/` (fonts, vendor icons, morphicons), `decks/`.
- `python tools/serve.py --port 8191 --auto-pdf` rebuilds on any change (no manual build). Screenshots to verify layouts: `.venv/bin/python tools/shot.py <slug>`.
- Secrets live in `data/` (git-ignored): never print or commit the PIN, `secret.key` or tokens.
- Setup on a fresh machine: `tools/setup.sh`.
