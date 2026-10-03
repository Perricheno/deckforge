---
name: deck-speech
description: Write the spoken defense/presentation text (speaker notes) for a deck in this repo, in the house style - long flowing formal sentences, no greeting, no "this slide shows", answering the assignment's required questions slide by slide. Use when the user asks for a speech, spich, speaker notes, defense text, or a shorter/longer/translated version of it.
---

# Speech text for a deck

Output goes to `decks/<slug>/speech.<lang>.md` (en, ru, kz). The phone remote renders it as a Markdown viewer, so the file format matters; it is never served publicly.

## File format
```
# Speech: <deck short name> (about N minutes)

## Slide 1
One flowing paragraph.

## Slide 2
...
```
One `## Slide N` heading per slide, in order, and nothing else the presenter would trip over (no tables, no nested lists, no stage directions in brackets). Keep bold only for a word the presenter must stress.

## House style (this is what the user approved)
- **Long, flowing sentences.** Join ideas with commas, "which", "because", "so", "while". Avoid chains of 5-8 word sentences. A slide is usually 2-4 sentences.
- **No greeting, no filler, no meta-talk.** Never write "this is our framework", "on this slide", "as you can see", "now let's move on". State the content directly ("In our framework, the user context influences...").
- **B2 formal English.** Common vocabulary, precise terms, no idioms. Spell out hypotheses and tests as "First..., second..., third...".
- **Answer the brief.** If the deck answers an assignment, map every required question to a slide and make sure the text says it explicitly: the chosen approach by name, why it was chosen and what it should achieve, hypotheses (or why none), what data exactly will be collected (name the scales/variables), sample size and duration, methods and instruments. Check the assignment text in the repo or the user's message and list any question left half-answered.
- **No references or citations** unless the user asks for them.
- **Never state invented numbers as facts.** If the deck contains illustrative values, the speech says so ("these figures are hypothetical").
- **Each slide ends cleanly.** The last slide closes with the conclusion, one implication, and "Thank you. We are ready for questions."

## Length and splitting
- English speaking pace: about 130 words per minute. 5 minutes is about 650 words, 3.5 minutes about 450.
- "Shorter by X%": cut content, not sentence length. Keep sentences long, drop secondary examples first, never drop an answer to a required question.
- Two presenters: put the split in the chat reply (e.g. "slides 1-3 first speaker"), not in the file.

## Languages
- Default English. Russian and Kazakh versions are natural rewrites, not word-for-word: same structure and numbers, shorter spoken sentences are fine. Kazakh terms: бәсекелестік артықшылық, жасанды интеллект, толықтырушы факторлар, жұмыс процестері, кадрлар, басқару, мәдениет, пилоттық жоба.
- File names: `speech.en.md`, `speech.ru.md`, `speech.kz.md`. The remote shows a language switch automatically.

## In the chat reply
When the user wants to read from a phone, send the text by slides as plain paragraphs (`Slide 1: ...`) without blank lines inside a slide and without markdown decoration. Add a short list of what you assumed or invented so the user can confirm it. Offer a 10-question Q&A prep only if asked.

## Checklist before saying done
1. Slide count matches the deck. 2. No meta-talk, no greeting. 3. Every required question answered explicitly. 4. Word count fits the time. 5. Invented details flagged. 6. File saved under `decks/<slug>/` (the server picks it up immediately; no build needed).
