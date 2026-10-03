# deck.json reference

```jsonc
{
  "title": "…", "subtitle": "one sentence for the gallery", "authors": ["A B", "C D"],
  "date": "2026-10", "tags": ["Strategy"], "minutes": 5, "order": 0, "hidden": false,
  "tag": "header label", "footer": "left footer", "footer_right": "right footer",  // right defaults to author surnames
  "accent": "#ff4b1f", "lang": "en", "pdf": "optional-name.pdf",
  "bg": "aurora", "bg_opts": {},                                // default scene for all slides (optional)
  "motion": {"speed": 1, "intensity": 1, "seed": null, "reduce": "respect", "scenes": {"aurora": {"color": "#3366ff"}}},
  "slides": [ { "layout": "…", … } ]
}
```
Text fields accept inline markup: `**bold**`, `*dim grey*`, `^^accent shine^^`, `` `code` ``.

## Slide fields (all layouts)
`layout`, `tag` (header label), `title` (animated word by word), `n` (section number shown before the title), `foot`, `foot_right`, `bg` + `bg_opts`, `decor`.
- `bg`: `aurora` | `grid` | `waves` | `orbits` | `particles`. `bg_opts` e.g. `{"alpha":0.7,"color":"#3366ff"}`; waves `{"y":0.9}`; grid `{"cols":40,"rows":22}`; orbits `{"x":0.8,"y":0.5,"speed":1}`; particles `{"count":46}`.
- `decor`: free-floating shapes `{"kind":"ring|dot|square|plus|line","x":62,"y":8,"size":70,"color":"#ff4b1f","opacity":0.5,"motion":"float:amp=10,per=7 spin:per=60"}` (x,y in % of the slide).

## Layouts
| layout | fields |
|---|---|
| `cover` | `eyebrow`, `title`, `meta:[[k,v]]` (authors are added automatically), `left:[blocks]`, `right:[blocks]` (grid: wide left column, 430 px right) |
| `flow` | `title`, `n`, `blocks:[…]` (use `flowcards`, `mod`, `html`), `columns:[[blocks],[blocks],…]` (bottom row, equal columns) |
| `split` | `title`, `n`, `cols:"1.4fr 1fr"`, `left:[blocks]`, `right:[blocks]`, `strip:[[k,v],…]` (bottom tiles), `center:true` |
| `pipeline` | `title`, `n`, `steps:[{icon,t,d,human?}]` (highlight jumps between steps), `cards:[blocks]` (bottom row), `cols:"1.1fr 1fr 1fr"` |
| `cards` | `title`, `n`, `lead` (right of the title), `cols`, `cards:[{icon,acc?,title,t,viz?:{kind:"converge"\|"decay"\|"packets"},cap}]`, `blocks:[…]` |
| `chart` | `title`, `n`, `left:[blocks]`, `chart:{…curve…}`, `cols:"1fr 520px"`, `blocks:[…]` |
| `compare` | `title`, `n`, `formula:[{icon,t,op?:"x"\|"=",out?}]`, `items:[{name,sub,rows:[{icon,label,v 0..1}]}]` (two firms/options; meters breathe, % follows), `out_label`, `cap` |
| `stats` | `title`, `n`, `lead`, `items:[{icon?,acc?,to,dec?,amp?,suffix?,label,bar? 0..1}]` (count up, then drift), `blocks:[…]` |
| `closing` | `eyebrow`, `title`, `takeaways:[{icon,acc?,title,t}]` (authors added) |
| `html` | `html` (escape hatch; avoid) |

## Blocks (`{"type": …}`; a plain string is a text block)
Any block may add `motion`, `kf`, `dur`, `pingpong` (see Motion).
- `text {t, cls?:"lead"|"small"|"cap"}` · `eyebrow {t}` · `bullets {items:[{b?,t}]}` · `note {icon?,t}` · `gap {icon?,b?,t}` · `mod {icon?,t}` (dashed callout)
- `minis {eyebrow?, items:[{icon,acc?,b,t}]}` · `notes {eyebrow?, items:[{b?,t,solid?}]}` · `mix {eyebrow?, boxes:[{t,s,r?}]}`
- `table {columns:[str|{h,w?,badge?}], rows:[[cell…]], cycle?}` cell = string | `{icon,acc?,t,s?}`; `badge` column renders `H1` pills (`!RQ` = dark). `cycle:true` highlights rows at random.
- `hmap {title, rows:[{b,from,to,d?,icon?}]}` · `datacards {items:[{icon,acc?,title,sub,bullets:[]}], merge?:{icon,title,t}}` · `strip {items:[[k,v]]}`
- `phone {name, sub, messages:[{t, me?, stars?, opts?:[…]}]}` (answers change on their own) · `rows {items:[{icon,acc?,title,t,bars?:[5 numbers],n}]}` · `timeline {segments:[[start%,width%,"ink"|"acc"]], ticks:[[k,v]], loop?}` · `funnel {title,rows:[[k,pct]],tips:[]}` · `pair {items:[block,block]}`
- `steps {items:[{icon,t,d}], label?, style?:"pipe"|"apipe"}` · `flowcards {nodes:[{icon,title,label,items:[],out?,subs?:[[b,t]]}]}` (boxes joined by flowing dots)
- `whisker {title, rows:[[label,mean,lo,hi]], min,max, axis, chips?:{title,items}, cap}` (confidence intervals that drift) · `guard {title, items:[{icon,b,t}], gauge?:{title,bands:[…],marker %,t}}` · `thr {title, rows:[[k,v]], joint?:["a","b","!result"]}`
- `curve` (use as `chart`): `{series:[{name,color:"acc"|"ink"|"faint"|"#hex",width?,fill?,period?,pts:[[x,y]…]}], baseline?, baseline_label?, y_label?, phases?:[{from,to,label,color}], cap?}` x,y in 0..100, y up. Smooth line + walking marker.
- `question {label,t,icons:[…]}` (dark card with morphing icon) · `subq {items:[[k,v]]}` · `glance {items:[[k,v]]}` · `toc {items:[{icon,t,pg}]}` · `hero {icons:[…],captions:[…]}` (orbiting, morphing) · `outline {items:[{icon,t,pg}]}` · `ticker {items:[…]}` (infinite marquee) · `firms` · `stats` · `cards` · `viz {kind}` · `html {html}`

## Motion (declarative, no code)
- `data-motion` / block `motion`: space-separated `name:key=val,key=val`. Names: `float` (amp, per), `drift` (amp, per), `pulse` (scale, per), `spin` (per, dir), `sway` (deg, per), `breathe` (depth, per), `wobble` (amp). Combine freely.
- Keyframes: block `kf:[{"t":0,"x":0,"y":0,"s":1,"r":0,"o":1,"ease":"inOut"},{"t":.5,"x":40}]`, `dur` seconds, `pingpong:true`. Props: x,y (px), s scale, r rotate (deg), o opacity. Easings: linear in out inOut inCubic outCubic inOutCubic outBack outElastic outBounce.
- Automatic: connectors (`flow`), curve markers, packets, cycling highlights, morphing icons, random answers, counters, drifting meters/intervals, tickers.
- Global tuning in deck `motion`: `speed`, `intensity` (amplitude of drifts), `seed` (reproducible randomness), `reduce` ("respect" default | "ignore"), `scenes:{name:{opts}}`.
- URL flags: `?pdf` static frame, `?thumb` chrome-less.

## Per-deck code (only when built-ins are not enough)
`decks/<slug>/plugin.js`, an ES module loaded after the engine:
```js
const DM = window.DeckMotion;
DM.register('heartbeat', { selector: '[data-heartbeat]', setup(el, api) { return t => { el.style.opacity = .6 + .4*Math.abs(Math.sin(t*2)); }; } });
DM.scene('stripes', (ctx, t, w, h, opts) => { /* draw on a 1280x720 canvas */ });   // then "bg":"stripes"
```
`api` has: `rand, rnd(a,b), ease(p,name), lerp, clamp, amp(v), every(el,fn), later(el,minS,maxS,fn), num(el,key,default), str(...), mk(svg,r,fill,stroke), ACC, INK, I (icons)`. Behaviors run only while their slide is visible and are skipped for PDFs. Use the `html` block (or `html` slide) to place elements with your data attributes.

## Icons available (camelCase)
activity arrowLeft arrowRight bot building2 chartBarBig chartColumn chartLine chartNoAxesColumnIncreasing check circleHelp clipboardList clock compass copy cpu database download equal eye factory fileDown fileText filter flaskConical gauge gitBranch gitMerge graduationCap layers lightbulb listChecks lockOpen lock messageCircle monitor repeat rocket route scale scanSearch search send shieldCheck sparkles sprout star tags target thumbsUp timer trendingDown userCheck users workflow x zap
More: `python tools/addicons.py chart-pie map-pin` (kebab-case Lucide ids), then use `chartPie`, `mapPin`.

## Remote, speech and URLs
- Deck: `/<slug>/`  ·  gallery: `/`  ·  presenter remote: `/admin/` (6-digit PIN) · PDF: `/<slug>/<pdf>`.
- Speaker notes: `decks/<slug>/speech.<lang>.md` with `## Slide N` headings (see the `deck-speech` skill).
- Viewers follow the presenter automatically while a phone is connected; a small round button (bottom-left of every deck) shows live status, a follow toggle, fullscreen, and the link to the remote.
