# deckforge

Presentations as data, with motion-design visuals that loop forever without repeating, a one-click PDF, a gallery home page, and a phone remote (numeric PIN, SSE) that drives every viewer's slides and shows your speaker notes.

```
decks/<slug>/deck.json      the deck (content only)
decks/<slug>/speech.en.md   speaker notes (shown on the phone remote)
decks/<slug>/plugin.js      optional custom motion behaviors
engine/                     theme, motion engine, viewer remote button, gallery, remote page
tools/                      build, server, pdf, screenshots, icons, pin
```

- `python3 tools/serve.py --port 8191 --auto-pdf` serves `dist/`, rebuilds on every change, never caches.
- Presenter: open `/admin/` on the phone, enter the 6-digit PIN, pick a deck. Viewers follow while the phone is connected.
- Claude Code skills in `.claude/skills/`: `deck-build` (create decks from JSON) and `deck-speech` (speaker text).
- Docs for authors: `.claude/skills/deck-build/reference.md`.

Setup: `tools/setup.sh`. Change the PIN: `python3 tools/setpin.py 123456`.
