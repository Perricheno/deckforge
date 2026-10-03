---
name: deck-build
description: Create or edit a presentation in this repo (deckforge). The deck is a short deck.json - never hand-written HTML/CSS/JS - and the engine adds layouts, looped motion graphics, PDF export, a phone remote and instant live updates. Use when the user asks for a presentation, slides, a deck, or changes to an existing one.
---

# Build a deck

You write **content only**: `decks/<slug>/deck.json`. The engine (layouts, blocks, motion, PDF, remote) already exists, so do not read engine source and do not write HTML. Read `reference.md` in this folder for every layout, block and motion option; copy from `decks/deckforge-showcase/deck.json` when you need a working example. This keeps the job cheap.

## Workflow
1. **Brief.** Get topic, audience, authors, duration, language, and the exact questions an assignment requires. Missing facts: ask once, or pick a sensible default and say so.
2. **Plan 5-9 slides.** One idea per slide. Map assignment questions to slides explicitly. Pick a layout per slide from `reference.md` (cover, flow, split, pipeline, cards, chart, compare, stats, closing).
3. **Write `decks/<slug>/deck.json`.** The server (service `deckforge`, port 8191) rebuilds on every request, so the page is live at `https://x.perricheno.com/<slug>/` about a second after saving. No build command, no cache.
4. **Check by eye.** `.venv/bin/python tools/shot.py <slug>` prints PNG paths; open them with the Read tool. Fix overflow (shorten text, change columns), overlaps, empty areas. Use `--mobile` once. Console errors must be `none`.
5. **PDF.** Generated automatically after a rebuild (`--auto-pdf`); to force: `.venv/bin/python tools/pdf.py <slug>`. The Download PDF button appears once the file exists.
6. **Speech.** Use the `deck-speech` skill and save `decks/<slug>/speech.en.md` so the phone remote can show it.
7. Tell the user the URL, the PIN reminder (`python tools/setpin.py <6 digits>` to change), and list what you invented (numbers, sample sizes) so they can confirm.

## The brief in the user's own keywords (treat these as the main rules)
**Interactive-style animated infographic · visually animated information · animated visual explanation · simulation · animated simulation-explanatory infographic · After Effects motion design · motion graphics · every visual on an infinite loop.**
- In practice: each slide is a **self-playing visual explanation**. Nobody has to click, drag or press anything (the presenter only advances slides). The visual itself runs a scenario (a simulation, a flow, a process, a comparison over time) and **explains systematically**: numbered phases or a stepper, labels that appear in the order of the story, live values, cause -> effect shown by motion, a caption per phase, then it loops cleanly.
- **These keywords are the rules, not a ceiling.** Do not limit yourself to the built-in blocks, layouts or this reference. When a story needs a bespoke visual, **write the code for it**: canvas 2D, SVG, WebGL, hundreds or thousands of lines per slide, particle systems, custom physics/economics models, custom easing, anything. Put it in the deck's `plugin.js` / `plugins/*.js` with `DeckMotion.custom('name', (el, api) => update)` and place it with a `custom` layer. Built-ins are only shortcuts.
- Quality bar: a stranger should understand the idea by watching the loop once, without reading paragraphs. See `decks/motion-design-nbk/plugin.js` (`economy`: a 250-line self-playing simulation with a model, particle flows, phase stepper, live values and a chart that draws itself) as the reference of effort and style.
- Always verify motion by sampling several moments: `/tmp` screenshots at different times (e.g. a script that opens the slide and screenshots at 3 s, 8 s, 13 s), and the PDF still frame (`poster`). Handle `api.STATIC` (PDF/reduced motion): draw the finished frame.

## Motion first (the user's brief: After Effects style motion design, everything looped)
- The user rejected template-looking decks (cards, icon grids, generic charts). Default to **`scene` slides**: kinetic type, drawn-on shapes, camera moves, counters and one explanatory visual per slide that tells a story. Use list/table layouts only when the content truly is a list or a table.
- Think like a motion designer: storyboard each slide as a 12-18 s loop with in/out points (see the recipe in `reference.md`), vary rhythm and layout between slides, and use a different theme/scene mix per deck so decks do not look alike.
- Visuals must explain something (relationships, sequence, change over time, geography), not decorate. Prefer the storytelling widgets (`map`, `lags`, `journey`, `erosion`) and `curve`; draw new custom illustrations as inline SVG shapes when needed.
- Real brands: take the palette from the brand's own site/logo (add a `[data-theme=...]` block), never invent logos.

## Design rules
- **Inter only**, weight and size carry hierarchy. One accent colour (`accent` in deck.json to change). Minimal, generous spacing, light theme.
- **Every slide has something that moves**: a `bg` scene (aurora, grid, waves, orbits, particles), a chart marker, packets/flow connectors, morphing icons, a counter, a ticker, or `decor` shapes. Vary scenes between slides; never put the same scene on every slide.
- **Content budget per slide** (1280x720): title 4-9 words, at most ~70 words of body text in total, at most 3 cards/columns, tables at most 5 rows. Dense is fine for academic defenses but check screenshots.
- Formal, plain language. No citations unless asked. No fabricated statistics: mark illustrative values ("Illustrative, not real data") in a caption.
- Use `*dim text*` for the grey second half of a title and `^^accent^^` sparingly (it shines).
- Icons are Lucide names in camelCase (see list in `reference.md`). Unknown icon -> the build fails with the fix: `python tools/addicons.py <kebab-name>`.
- Custom motion: `motion:"float:amp=8,per=6"` on any block, `kf` keyframes, or a per-deck `plugin.js` (see reference). Prefer the built-ins.

## Rules for editing
- Keep the slug stable (it is the URL). Changing `title` is fine.
- Legacy decks (`"legacy": true`, `legacy.html`) are standalone pages; do not convert them unless asked.
- Never commit `dist/`, `data/`, PDFs or `.venv/` (git-ignored). Never print or commit the PIN or `data/secret.key`.
- If the build fails, the old site keeps serving; read the error with `journalctl -u deckforge -n 20 --no-pager` or run `python tools/build.py`.
