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

## Themes and design variety
Set `"theme"` on the deck and/or on any slide (the page chrome follows the slide): `paper` (default light), `sand`, `sky`, `mono`, `ink` (dark navy + gold), `night` (dark + cyan), `nbk` and `nbk-dark` (National Bank of Kazakhstan: logo green #00471C, gold #9A7500, slate #2f3c49). Mix themes between slides, and mix layouts and `bg` scenes, so decks do not look alike. New palette = add a `[data-theme=name]{...}` block of CSS variables in `engine/theme.add.css`.
Scenes: `aurora grid waves orbits particles steppe`.

## Scene layout: real motion design (preferred for anything that must not look like a template)
`layout:"scene"` is an After Effects style composition: free layers on a 1280x720 canvas, each with an in point (`at`) and out point (`out`) on a **looping timeline** (`loop` seconds). Everything repeats seamlessly forever. Use `"chrome":false` for full-bleed (no header/footer).
```jsonc
{"layout":"scene","chrome":false,"theme":"nbk-dark","bg":"steppe","loop":14,"poster":8,   // poster = still frame used for PDF/thumbnails (all layers visible)
 "camera":[{"t":0,"s":1,"x":0,"y":0},{"t":7,"s":1.04,"x":-16,"y":-6},{"t":14,"s":1,"x":0,"y":0}],   // slow push, returns to start for a seamless loop
 "layers":[ …layers… ]}
```
Common layer fields: `type`, `x`,`y` (px, top-left; `anchor`: tl tc tr cl c cr bl bc br), `at`, `out`, `in`, `outAnim`, `dur`, `stagger`, `z`, `loop` (ambient `data-motion` string, e.g. `"float:amp=6,per=8"`), `anim` (keyframes `[{t,x,y,s,r,o,b,ease}]` in composition time).
- `in` presets: `rise mask fade pop blur slide slider drop zoom wipe draw none`. `outAnim`: `fade rise mask shrink cut blur wipe zoom` (default: fade just before the loop ends). `mask` = text slides up from behind a clip.
- `text`: `t` (markup `*dim*`, `^^accent^^`, `\n` line breaks), `size`, `weight`, `spacing` (em), `lh`, `color` (ink mute faint acc body on or any CSS colour), `align`, `w` (wrap width), `upper`, `split`: `chars|words|lines` (each piece animates in turn, `stagger` seconds).
- `shape`: `shape` rect|circle|ring|line|plus|path (`d`,`vb`), `w`,`h`,`fill`,`stroke`,`sw`,`r`,`opacity`; `in:"draw"` draws the stroke on (trim path), `in:"wipe"` reveals it.
- `widget`: `block` = any block (map, lags, journey, erosion, baiterek, curve, whisker…), `w`; add `draw:true` to draw a map outline on. Widgets keep their own looping behaviours.
- `icon`: `name`, `size`, `sw`, `color`, `seq:[{at,to}]` morphs through icons on the timeline. `counter`: `from`,`to`,`at`,`cdur`,`dec`,`prefix`,`suffix`,`size`,`color`.
**Storyboard recipe** (what a good scene does): 0-1 s eyebrow fades in; 0.3-2 s headline rises word by word (`mask`); 2-3 s a rule wipes in and the sub-line fades; 3-6 s the visual (map/chart/diagram) draws on and starts its own loop; last 0.6 s everything fades so the loop restarts cleanly. Tell one idea per scene with a visual that *explains* it (a signal crossing a country, a lag between a decision and prices, a payment travelling through banks, coins losing value year by year), not a grid of icons.

## Storytelling widgets
- `map {…, signal:true, label_size}`: waves leave the HQ and light each city on arrival. · `lags {rows:[{t,d,kind:"step"|"rise"|"fall",delay,tau,acc?}], shock?, shock_label, ticks?, loop, cap}`: impulse response; a cursor sweeps time and each row lights up when it reacts. · `journey {nodes:[{kind:"phone"|"bank"|"nbk"|"shop",t,d}], go, back}`: a request travels out and the confirmation returns. · `erosion {rates:[5,10], years, loop, cap}`: coins shrink year by year (exact arithmetic 100/(1+r)^y). · `baiterek {}`: line illustration with a slow sun.

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
| `poster` | editorial cover: `eyebrow`, `title` (very large), `sub`, `left:[blocks]`, `art:[blocks]` (right, e.g. a `map`), `ticker:[…]`, `cols` |
| `spotlight` | text left, one big visual right: `title`, `n`, `lead`, `left:[blocks]`, `right:[blocks]` (`map`, `dial`, `iconwall`, `curve`…), `cols:"350px 1fr"` |
| `history` | timeline with a travelling pulse that lights each event: `title`, `n`, `lead`, `events:[{year,icon?,title,t}]`, `loop` seconds |
| `scene` | see the section above (layers, loop, poster, camera, chrome:false) |
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
- `map {points:["Astana","Almaty",…] or [{name,lat,lon}], hq:"Astana", arcs:"hub"|[[a,b]], labels:true|false|"hq"|{name:"left|right|top|bottom"}, cycle:true, graticule:true}` Kazakhstan outline (Natural Earth, public domain) with pulsing HQ, flowing arcs, cities highlighted in turn. Built-in cities: Astana Almaty Shymkent Aktobe Atyrau Aktau Karaganda Pavlodar Kostanay Oskemen Kyzylorda Uralsk Taraz Turkistan Semey Petropavl Kokshetau Taldykorgan Zhezkazgan Baikonur.
- `dial {value 0..1, amp?, title, cap}` gauge whose needle breathes (label illustrative values) · `iconwall {cols, items:[{icon|icons:[a,b], t, d}]}` (several icons = they morph) · `morphline {icons:[…], size?}` row of morphing icons · `bigtype {t}`
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
Custom drawn set (24x24, made for this project, `assets/vendor/icons.custom.js`): tenge nbk baiterek shanyrak yurt rate inflation digitalTenge card qr shieldTenge network kazakhstan sun. Add your own by writing an IconNode there (same format as Lucide); morphicons morphs between any two.
More Lucide: `python tools/addicons.py chart-pie map-pin` (kebab-case Lucide ids), then use `chartPie`, `mapPin`.

## Remote, speech and URLs
- Deck: `/<slug>/`  ·  gallery: `/`  ·  presenter remote: `/admin/` (6-digit PIN) · PDF: `/<slug>/<pdf>`.
- Speaker notes: `decks/<slug>/speech.<lang>.md` with `## Slide N` headings (see the `deck-speech` skill).
- Viewers follow the presenter automatically while a phone is connected; a small round button (bottom-left of every deck) shows live status, a follow toggle, fullscreen, and the link to the remote.
