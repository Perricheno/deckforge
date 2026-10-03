#!/usr/bin/env python3
"""deckforge build: decks/<slug>/deck.json -> dist/ (static site).

A deck is plain data (see .claude/skills/deck-build/reference.md). Layouts and
blocks below turn it into HTML that already contains the looped motion graphics
(engine/motion.js), so authors never write HTML, CSS or JS.

Legacy decks (decks/<slug>/legacy.html + deck.json with "legacy": true) are copied as-is.
"""
import html, json, os, re, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECKS, ENGINE, ASSETS, DIST = ROOT / "decks", ROOT / "engine", ROOT / "assets", ROOT / "dist"
esc = html.escape

# ----------------------------------------------------------------- text helpers
def rich(s):
    """**bold**  *dim*  ^^accent^^  `code`"""
    s = esc(str(s), quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\^\^(.+?)\^\^", r'<span class="hl">\1</span>', s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r'<span class="dim">\1</span>', s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s

def kinetic(s):
    """Word-by-word mask reveal; keeps *dim* and ^^accent^^ styling per word."""
    parts = re.findall(r"\^\^.+?\^\^|\*\*.+?\*\*|(?<!\*)\*(?!\*).+?(?<!\*)\*(?!\*)|[^*^]+", str(s))
    out, i = [], 0
    for p in parts:
        cls = ""
        if p.startswith("^^"): cls, p = "hl", p[2:-2]
        elif p.startswith("**"): cls, p = "b", p[2:-2]
        elif p.startswith("*"): cls, p = "dim", p[1:-1]
        for w in p.split():
            c = f' class="wi {cls}"' if cls else ' class="wi"'
            out.append(f'<span class="w"><span{c} style="--i:{i}">{esc(w, quote=False)}</span></span>')
            i += 1
    return " ".join(out)

def ic(name, size=16, sw=2, extra=""):
    return f'<morph-icon data-i="{esc(name)}" size="{size}" stroke-width="{sw}"{extra}></morph-icon>'

def ico(name, acc=False, dark=False, size=16, style=""):
    c = "ico" + (" acc" if acc else "") + (" dark" if dark else "")
    st = f' style="{style}"' if style else ""
    return f'<div class="{c}"{st}>{ic(name, size)}</div>'

def rise(d, extra=""):
    return f'class="rise{(" " + extra) if extra else ""}" style="--d:{d}"'

# ----------------------------------------------------------------- blocks
def b_text(b):
    return f'<p class="{b.get("cls","")}">{rich(b["t"])}</p>'

def b_eyebrow(b):
    return f'<div class="eyebrow" style="margin-bottom:{b.get("mb",8)}px">{rich(b["t"])}</div>'

def b_bullets(b):
    items = "".join(f'<li>{"<b>%s</b> " % rich(i["b"]) if i.get("b") else ""}{rich(i["t"])}</li>' for i in b["items"])
    return f'<ul class="b">{items}</ul>'

def b_note(b):
    return f'<div class="note">{ico(b.get("icon","lightbulb"))}<span>{rich(b["t"])}</span></div>'

def b_gap(b):
    return f'<div class="gap">{ico(b.get("icon","eye"))}<p>{"<b>%s</b> " % rich(b["b"]) if b.get("b") else ""}{rich(b["t"])}</p></div>'

def b_mod(b):
    return f'<div class="mod">{ic(b.get("icon","scale"))}<span>{rich(b["t"])}</span></div>'

def b_minis(b):
    head = f'<div class="eyebrow" style="margin-bottom:8px">{rich(b["eyebrow"])}</div>' if b.get("eyebrow") else ""
    rows = "".join(f'<div class="mini">{ico(i.get("icon","check"), i.get("acc"), size=14)}<div><b>{rich(i["b"])}</b><p>{rich(i["t"])}</p></div></div>' for i in b["items"])
    return head + rows

def b_notes(b):
    head = f'<div class="eyebrow" style="margin-bottom:8px">{rich(b["eyebrow"])}</div>' if b.get("eyebrow") else ""
    rows = "".join(f'<div class="notc"{" style=&quot;border-style:solid;border-color:var(--ink)&quot;" if i.get("solid") else ""}>{"<b>%s</b> " % rich(i["b"]) if i.get("b") else ""}{rich(i["t"])}</div>'.replace("&quot;", '"') for i in b["items"])
    return head + rows

def b_mix(b):
    parts = []
    for i, x in enumerate(b["boxes"]):
        if i:
            parts.append(ic("gitMerge" if i == 1 else "arrowRight"))
        parts.append(f'<div class="box{" r" if x.get("r") else ""}">{rich(x["t"])}<small>{rich(x.get("s",""))}</small></div>')
    head = f'<div class="eyebrow" style="margin-bottom:8px">{rich(b["eyebrow"])}</div>' if b.get("eyebrow") else ""
    return head + f'<div class="mix">{"".join(parts)}</div>'

def b_table(b):
    cols = b["columns"]
    th = "".join(f'<th{" style=&quot;width:%s&quot;" % c["w"] if isinstance(c, dict) and c.get("w") else ""}>{rich(c["h"] if isinstance(c, dict) else c)}</th>'.replace("&quot;", '"') for c in cols)
    trs = []
    for r in b["rows"]:
        tds = []
        for ci, cell in enumerate(r):
            c = cols[ci] if isinstance(cols[ci], dict) else {}
            if c.get("badge"):
                tds.append(f'<td><span class="hn{" q" if str(cell).startswith("!") else ""}">{esc(str(cell).lstrip("!"))}</span></td>')
            elif isinstance(cell, dict):   # {icon, t, s}
                tds.append(f'<td><span class="k">{ico(cell.get("icon","check"), cell.get("acc"), size=15)}<span>{rich(cell["t"])}{"<small>%s</small>" % rich(cell["s"]) if cell.get("s") else ""}</span></span></td>')
            else:
                tds.append(f"<td>{rich(cell)}</td>")
        trs.append(f'<tr>{"".join(tds)}</tr>')
    cyc = " data-cycle" if b.get("cycle") else ""
    cls = "gt" + (" hy" if any(isinstance(c, dict) and c.get("badge") for c in cols) else "")
    return f'<div class="tbl {cls}"><table><thead><tr>{th}</tr></thead><tbody{cyc}>{"".join(trs)}</tbody></table></div>'

def b_hmap(b):
    rows = "".join(f'<div class="hm"><span class="hb">{esc(r["b"])}</span><span class="c">{rich(r["from"])}</span>{ic(r.get("icon","arrowRight"),14)}<span class="c o">{rich(r["to"])}</span><span class="d">{rich(r.get("d",""))}</span></div>' for r in b["rows"])
    return f'<div class="hmap"><div class="eyebrow" style="margin:10px 0 8px">{rich(b.get("title",""))}</div>{rows}</div>'

def b_datacards(b):
    out = []
    for c in b["items"]:
        li = "".join(f"<li>{rich(x)}</li>" for x in c.get("bullets", []))
        out.append(f'<div class="card dc"><div class="hd">{ico(c.get("icon","database"), c.get("acc"))}<div><h3>{rich(c["title"])}</h3><small>{rich(c.get("sub",""))}</small></div></div><ul>{li}</ul></div>')
    if b.get("merge"):
        m = b["merge"]
        out.append(f'<div class="dcw"><svg viewBox="0 0 400 28" preserveAspectRatio="none"><path class="flow" d="M200 0V28" fill="none" stroke="#a9a9a2" stroke-width="1.5"/></svg></div>')
        out.append(f'<div class="card merge">{ico(m.get("icon","database"))}<div><h3>{rich(m["title"])}</h3><p>{rich(m["t"])}</p></div></div>')
    return f'<div style="display:flex;flex-direction:column;gap:8px">{"".join(out)}</div>'

def b_strip(b):
    return '<div class="sample">' + "".join(f'<div><b>{rich(k)}</b>{rich(v)}</div>' for k, v in b["items"]) + "</div>"

def b_phone(b):
    msgs = []
    for m in b["messages"]:
        extra = ""
        if m.get("stars"):
            extra = '<div class="stars" data-rand="stars">' + "".join(ic("star") for _ in range(5)) + "</div>"
        if m.get("opts"):
            extra = '<div class="opts" data-rand="opts">' + "".join(f"<span>{rich(o)}</span>" for o in m["opts"]) + "</div>"
        cls = "msg me" if m.get("me") else "msg"
        msgs.append(f'<div class="{cls}">{rich(m["t"])}{extra}</div>')
    typing = '<div class="typing"><i></i><i></i><i></i></div>'
    return (f'<div class="phone"><div class="bar"><div class="av">{ic("bot",14)}</div><div><b>{rich(b.get("name","Bot"))}</b><small>{rich(b.get("sub",""))}</small></div></div>'
            f'<div class="chat">{"".join(msgs)}{typing}</div></div>')

def _likert(vals):
    mx = max(vals)
    return '<div class="likert">' + "".join(f'<i class="{"pk" if v == mx else ""}" style="--h:{v}"></i>' for v in vals) + "</div>"

def b_rows(b):
    out = []
    for r in b["items"]:
        out.append(f'<div class="card bl">{ico(r.get("icon","check"), r.get("acc"))}<div><h3>{rich(r["title"])}</h3><p>{rich(r.get("t",""))}</p></div>{_likert(r["bars"]) if r.get("bars") else "<div></div>"}<span class="n">{rich(r.get("n",""))}</span></div>')
    return f'<div class="blocks" style="flex:1">{"".join(out)}</div>'

def b_timeline(b):
    segs = b["segments"]   # [[start%, width%, 'ink'|'acc'], ...]
    sg = "".join(f'<div class="seg" style="left:{a}%;width:{w}%;background:{"var(--acc)" if c=="acc" else "var(--ink)"};{"opacity:.55" if c=="acc" else ""}"></div>' for a, w, c in segs)
    ticks = "".join(f'<div><b>{rich(k)}</b>{rich(v)}</div>' for k, v in b["ticks"])
    return (f'<div class="tl"><div class="track">{sg}<div class="dotm" data-loop="{b.get("loop",11)}" style="left:0"></div></div>'
            f'<div class="ticks" style="grid-template-columns:repeat({len(b["ticks"])},1fr)">{ticks}</div></div>')

def b_funnel(b):
    rows = "".join(f'<div class="fn"><span>{rich(k)}</span><div class="t"><i style="width:{v}%"></i></div><em>{v}%</em></div>' for k, v in b["rows"])
    tips = "".join(f"<span>{rich(t)}</span>" for t in b.get("tips", []))
    return f'<div class="boost"><div class="eyebrow">{rich(b.get("title",""))}</div>{rows}<div class="tips">{tips}</div></div>'

def b_pair(b):
    return '<div class="two">' + "".join(render_block(x) for x in b["items"]) + "</div>"

def b_whisker(b):
    mn, mx = b.get("min", 1), b.get("max", 7)
    f = lambda v: (v - mn) / (mx - mn) * 100
    rows = "".join(
        f'<div class="sc" data-m="{m}" data-lo="{lo}" data-hi="{hi}" data-min="{mn}" data-max="{mx}"><span>{rich(n)}</span><div class="rail"><i class="wh" style="left:{f(lo):.1f}%;width:{f(hi)-f(lo):.1f}%"></i><i class="dt" style="left:{f(m):.1f}%"></i></div><em>{m:.1f}</em></div>'
        for n, m, lo, hi in b["rows"])
    axis = "".join(f"<span>{a}</span>" for a in b.get("axis", [mn, (mn + mx) / 2, mx]))
    chips = ""
    if b.get("chips"):
        chips = f'<div class="qc"><b>{rich(b["chips"].get("title",""))}</b>' + "".join(f"<span>{rich(c)}</span>" for c in b["chips"]["items"]) + "</div>"
    return (f'<div class="card themes"><h3>{rich(b["title"])}</h3><div class="axs"><span></span><div>{axis}</div><span></span></div>{rows}'
            f'<p class="cap" style="margin:6px 0 0">{rich(b.get("cap",""))}</p>{chips}</div>')

def b_guard(b):
    li = "".join(f'<li>{ic(i.get("icon","check"),15)}<span><b>{rich(i["b"])}</b> {rich(i["t"])}</span></li>' for i in b["items"])
    g = ""
    if b.get("gauge"):
        gg = b["gauge"]
        labels = gg["bands"]
        bands = "".join('<i style="width:%.1f%%;background:%s"></i>' % (100 / len(labels), c) for c, _ in zip(["#e5e5df", "#cfcfc8", "#a9a9a2", "#6f6f69", "#141412", "#141412"][:len(labels)], labels))
        g = (f'<div class="kap"><div class="eyebrow" style="margin-bottom:8px">{rich(gg["title"])}</div><div class="ks">{bands}<b data-base="{gg.get("marker",50)}" style="left:{gg.get("marker",50)}%"></b></div>'
             f'<div class="kl">{"".join(f"<span style=&quot;width:{100/len(labels):.1f}%&quot;>{rich(l)}</span>" for l in labels)}</div><p class="cap" style="margin-top:6px">{rich(gg.get("t",""))}</p></div>').replace("&quot;", '"')
    return f'<div class="card guard"><h3>{rich(b["title"])}</h3><ul>{li}</ul>{g}</div>'

def b_thr(b):
    rows = "".join(f"<tr><td>{rich(k)}</td><td>{rich(v)}</td></tr>" for k, v in b["rows"])
    j = ""
    if b.get("joint"):
        parts = []
        for i, x in enumerate(b["joint"]):
            if i:
                parts.append('<span class="arr">→</span>')
            o = x.startswith("!")
            parts.append(f'<span class="b{" o" if o else ""}">{rich(x.lstrip("!"))}</span>')
        j = f'<div class="joint">{"".join(parts)}</div>'
    return f'<div class="card thr"><h3>{rich(b["title"])}</h3><table><tbody>{rows}</tbody></table>{j}</div>'

def b_curve(b):
    """Smooth multi-series chart. pts are [x,y] in 0..100 (y up). Markers walk the lines."""
    W, H, X0, X1, Y0, Y1 = 480, 200, 30, 470, 176, 8
    X = lambda x: X0 + x / 100 * (X1 - X0)
    Y = lambda y: Y0 - y / 100 * (Y0 - Y1)
    def path(pts):
        P = [(X(x), Y(y)) for x, y in pts]
        d = f"M{P[0][0]:.1f} {P[0][1]:.1f}"
        for i in range(len(P) - 1):
            p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        return d, P
    col = {"acc": "#ff4b1f", "ink": "#141412", "faint": "#a9a9a2"}
    svg = [f'<path class="gr" d="M{X0} 24H{X1}M{X0} 72H{X1}M{X0} 128H{X1}"/><path class="ax" d="M{X0} 8V{Y0}H{X1}"/>']
    if b.get("baseline") is not None:
        svg.append(f'<path d="M{X0} {Y(b["baseline"]):.1f}H{X1}" stroke="#a9a9a2" stroke-dasharray="4 5"/>')
    legend = []
    for k, s in enumerate(b["series"]):
        c = col.get(s.get("color", "ink"), s.get("color"))
        d, P = path(s["pts"])
        if s.get("fill") is not None and b.get("baseline") is not None:
            svg.append(f'<path d="{d}L{P[-1][0]:.1f} {Y(b["baseline"]):.1f}L{P[0][0]:.1f} {Y(b["baseline"]):.1f}Z" fill="{c}" fill-opacity="{s["fill"]}"/>')
        svg.append(f'<path class="ln draw" pathLength="1" stroke="{c}" stroke-width="{s.get("width",2)}" d="{d}"/>')
        svg.append(f'<path class="mk" data-p="{s.get("period",10+3*k)}" data-ph="{.4*k}" data-c="{c}" data-r="{5 if k==0 else 3.5}" d="{d}" fill="none" stroke="none"/>')
        legend.append(f'<span><i style="background:{c}"></i>{rich(s["name"])}</span>')
    for ph in b.get("phases", []):
        a, z = X(ph["from"]), X(ph["to"])
        c = col.get(ph.get("color", "ink"))
        svg.append(f'<path d="M{a:.0f} 184V194M{z:.0f} 184V194M{a:.0f} 189H{z:.0f}" stroke="{c}"/><text class="t" x="{(a+z)/2:.0f}" y="199" text-anchor="middle" style="fill:{c}">{esc(ph["label"].upper())}</text>')
    if b.get("y_label"):
        svg.append(f'<text class="t" x="38" y="14">{esc(b["y_label"].upper())}</text>')
    if b.get("baseline_label"):
        svg.append(f'<text class="t" x="{X1-4}" y="{Y(b["baseline"])+14:.0f}" text-anchor="end">{esc(b["baseline_label"].upper())}</text>')
    return (f'<div class="card chart"><div class="legend">{"".join(legend)}</div><svg viewBox="0 0 {W} 206" width="100%">{"".join(svg)}</svg>'
            f'<p class="cap" style="margin-top:4px">{rich(b.get("cap",""))}</p></div>')

def b_viz(b):
    """Small explanatory graphics for cards: converge | decay | packets."""
    k = b["kind"]
    if k == "converge":
        s = ('<path class="gr" d="M0 20H240M0 40H240M0 60H240"/><path class="ax" d="M0 74H240"/>'
             '<path class="ln draw" pathLength="1" d="M0 66C60 56 130 24 236 12" opacity=".3"/><path class="ln draw" pathLength="1" d="M0 56C60 50 140 22 236 13" opacity=".55"/>'
             '<path class="ln draw mk" data-p="8.3" data-r="3.5" pathLength="1" d="M0 44C70 42 150 20 236 14"/>')
        return f'<div class="viz"><svg viewBox="0 0 240 76">{s}</svg></div>'
    if k == "decay":
        s = ('<path class="gr" d="M0 20H240M0 40H240M0 60H240"/><path class="ax" d="M0 74H240"/><path d="M0 8C56 48 120 66 236 70V74H0Z" fill="#ff4b1f" fill-opacity=".09"/>'
             '<path class="ln draw mk" data-p="6.3" data-c="#ff4b1f" data-r="4" pathLength="1" stroke="#ff4b1f" d="M0 8C56 48 120 66 236 70"/>')
        return f'<div class="viz"><svg viewBox="0 0 240 76">{s}</svg></div>'
    if k == "packets":
        pk = json.dumps({"from": [[34, 16], [34, 38], [34, 60]], "mid": [90, 38], "out": [200, 38]})
        s = ('<g stroke="#a9a9a2" stroke-width="1.2" fill="none"><path d="M34 16L90 38M34 38H90M34 60L90 38M150 38H200"/></g>'
             '<g fill="#fff" stroke="#141412" stroke-width="1.3"><circle cx="24" cy="16" r="9"/><circle cx="24" cy="38" r="9"/><circle cx="24" cy="60" r="9"/></g>'
             '<g font-size="9.5" font-weight="600" text-anchor="middle" fill="#141412"><text x="24" y="19.5">A</text><text x="24" y="41.5">B</text><text x="24" y="63.5">C</text></g>'
             '<rect x="90" y="24" width="60" height="28" rx="8" fill="#141412"/><text x="120" y="42" font-size="10.5" font-weight="500" text-anchor="middle" fill="#fff">Same AI</text>'
             '<rect x="200" y="24" width="36" height="28" rx="8" fill="#ff4b1f"/><path d="M210 38l5 5 11-11" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        return f'<div class="viz"><svg viewBox="0 0 240 76" data-packets=\'{pk}\'>{s}</svg></div>'
    return ""

def b_firms(b):
    out = []
    for fi, f in enumerate(b["items"]):
        rows = "".join(f'<div class="mrow">{ic(r.get("icon","check"),16)}{rich(r["label"])}<div class="meter"><i data-v="{r["v"]}" style="--v:{r["v"]}"></i></div></div>' for r in f["rows"])
        avg = round(sum(r["v"] for r in f["rows"]) / len(f["rows"]) * 100)
        out.append(f'<div class="card firm {"b" if fi else "a"}"><div class="fh"><h3>{rich(f["name"])}</h3><span class="cap">{rich(f.get("sub",""))}</span></div>{rows}'
                   f'<div class="outrow"><span class="cap">{rich(b.get("out_label","Result"))}</span><span class="big" data-auto>{avg}%</span></div></div>')
    return f'<div class="firms">{"".join(out)}</div>'

def b_stats(b):
    cards = []
    for s in b["items"]:
        suf = f'<small>{esc(s["suffix"])}</small>' if s.get("suffix") else ""
        bar = f'<div class="bar"><i data-v="{s["bar"]}" style="--v:{s["bar"]}"></i></div>' if s.get("bar") is not None else ""
        ic_ = ico(s["icon"], s.get("acc"), size=16) if s.get("icon") else ""
        cards.append(f'<div class="card stat">{ic_}<div class="val" data-to="{s["to"]}" data-dec="{s.get("dec",0)}" data-amp="{s.get("amp",0)}"><span class="num">{s["to"]}</span>{suf}</div><div class="lbl">{rich(s["label"])}</div>{bar}</div>')
    return f'<div class="stats" style="--n:{len(b["items"])}">{"".join(cards)}</div>'

def b_flowcards(b):
    """Framework boxes joined by animated connectors."""
    nodes, parts = b["nodes"], []
    for i, n in enumerate(nodes):
        if i:
            parts.append('<div class="conn"><svg viewBox="0 0 28 12"><path class="flow" d="M0 6H26" stroke="#a9a9a2" fill="none" stroke-width="1.5"/><path d="M21 1l5 5-5 5" stroke="#a9a9a2" fill="none" stroke-width="1.5"/></svg></div>')
        subs = ""
        if n.get("subs"):
            subs = '<div class="sub3">' + "".join(f"<div><b>{rich(a)}</b>{rich(c)}</div>" for a, c in n["subs"]) + "</div>"
        li = "".join(f"<li>{rich(x)}</li>" for x in n.get("items", []))
        parts.append(f'<div class="card fb{" out" if n.get("out") else ""}"><h3>{ico(n.get("icon","layers"), n.get("out"), size=14, style="width:28px;height:28px;border-radius:8px")}{rich(n["title"])}</h3>'
                     f'<span class="lab">{rich(n.get("label",""))}</span>{subs}<ul>{li}</ul></div>')
    cols = " ".join("1fr" if i % 2 == 0 else "28px" for i in range(len(nodes) * 2 - 1))
    return f'<div class="fw" style="grid-template-columns:{cols}">{"".join(parts)}</div>'

def b_steps(b):
    """Pipeline of cards with a highlight that jumps between steps."""
    cls = b.get("style", "pipe")
    out = []
    for i, s in enumerate(b["items"]):
        if cls == "apipe":
            out.append(f'<div class="ag{" hum" if s.get("human") else ""}"><span class="k">{i+1}</span>{ico(s["icon"], size=16)}<b>{rich(s["t"])}</b><span>{rich(s.get("d",""))}</span></div>')
        else:
            out.append(f'<div class="st">{ico(s["icon"], size=16)}<b>{rich(s["t"])}</b><span>{rich(s.get("d",""))}</span></div>')
    lab = f'<div class="eyebrow" style="margin:4px 0 8px">{rich(b["label"])}</div>' if b.get("label") else ""
    return f'{lab}<div class="{cls}" style="--n:{len(b["items"])}" data-cycle>{"".join(out)}</div>'

def b_question(b):
    icons = b.get("icons", ["messageCircle"])
    return (f'<div class="card rq"><div class="rqh"><div class="eyebrow">{rich(b.get("label",""))}</div><div class="rqi">'
            f'<morph-icon data-i="{icons[0]}" data-morph="{",".join(icons)}" size="20" stroke-width="1.75"></morph-icon></div></div><p>{rich(b["t"])}</p></div>')

def b_subq(b):
    return "".join(f'<div class="card sq"><i>{rich(k)}</i><p>{rich(v)}</p></div>' for k, v in b["items"])

def b_glance(b):
    return '<div class="glance">' + "".join(f"<div><b>{rich(k)}</b>{rich(v)}</div>" for k, v in b["items"]) + "</div>"

def b_toc(b):
    return '<div class="toc">' + "".join(f'<div>{ic(i.get("icon","layers"))}<b>{rich(i["t"])}</b><span>{rich(i.get("pg",""))}</span></div>' for i in b["items"]) + "</div>"

def b_hero(b):
    icons = b["icons"]
    caps = b.get("captions", [])
    return (f'<div class="hero orb"><div class="core"><morph-icon data-i="{icons[0]}" data-morph="{",".join(icons)}" data-caps="{"|".join(caps)}" data-cap-el="#heroCap" size="32" stroke-width="1.5"></morph-icon></div>'
            f'<div class="name" id="heroCap">{esc(caps[0]) if caps else ""}</div></div>')

def b_outline(b):
    return '<div class="card outline">' + "".join(f'<div><i>{k+1}</i>{ic(i.get("icon","layers"))}{rich(i["t"])}<span class="pg">{rich(i.get("pg",""))}</span></div>' for k, i in enumerate(b["items"])) + "</div>"

def b_ticker(b):
    items = "".join(f"<span>{rich(t)}</span>" for t in b["items"])
    return f'<div class="ticker"><div class="tr">{items}{items}</div></div>'

def b_cards(b):
    cols = b.get("cols", 3)
    cs = []
    for k, c in enumerate(b["items"]):
        viz = b_viz(c["viz"]) if c.get("viz") else ""
        cap = f'<p class="cap">{rich(c["cap"])}</p>' if c.get("cap") else ""
        cs.append(f'<div class="card c3"><div class="row">{ico(c.get("icon","layers"), c.get("acc"))}<span class="n">{k+1:02d}</span></div><div><h3>{rich(c["title"])}</h3><p class="small" style="margin-top:4px">{rich(c.get("t",""))}</p></div>{viz}{cap}</div>')
    return f'<div class="cards3" style="grid-template-columns:repeat({cols},1fr)">{"".join(cs)}</div>'

def b_html(b):
    return b["html"]

BLOCKS = {k[2:]: v for k, v in globals().items() if k.startswith("b_")}

def render_block(b):
    if isinstance(b, str):
        b = {"type": "text", "t": b}
    t = b.get("type", "text")
    if t not in BLOCKS:
        raise ValueError(f"unknown block type {t!r}; known: {', '.join(sorted(BLOCKS))}")
    h = BLOCKS[t](b)
    if b.get("motion") or b.get("kf"):
        attrs = ""
        if b.get("motion"): attrs += f' data-motion="{esc(b["motion"])}"'
        if b.get("kf"): attrs += f' data-kf="{esc(json.dumps(b["kf"]))}"'
        if b.get("dur"): attrs += f' data-dur="{b["dur"]}"'
        if b.get("pingpong"): attrs += " data-pingpong"
        h = f'<div class="fx"{attrs}>{h}</div>'
    return h

def blocks(lst, d0=1):
    return "".join(f'<div class="rise" style="--d:{d0+i}">{render_block(b)}</div>' for i, b in enumerate(lst or []))

# ----------------------------------------------------------------- slide chrome
def title_html(s, tag="h2"):
    if not s.get("title"):
        return ""
    n = f'<span class="n">{esc(str(s["n"]))}</span>' if s.get("n") else ""
    return f'<{tag} class="kin rise" style="--d:0">{n}{kinetic(s["title"])}</{tag}>'

def amb_html(s, deck):
    bg = s.get("bg", deck.get("bg"))
    if not bg:
        return ""
    o = s.get("bg_opts", deck.get("bg_opts"))
    oa = f" data-opts=\"{esc(json.dumps(o))}\"" if o else ""
    return f'<canvas class="amb" data-amb="{esc(bg)}"{oa} width="2560" height="1440"></canvas>'

def decor_html(s):
    """Free-floating motion shapes: {kind: ring|dot|square|plus|line, x,y (%), size (px), color, opacity, motion, kf, dur}"""
    out = []
    for d in s.get("decor", []):
        st = f'left:{d.get("x",50)}%;top:{d.get("y",50)}%;width:{d.get("size",60)}px;height:{d.get("size",60)}px;'
        if d.get("color"): st += f'--dc:{d["color"]};'
        if d.get("opacity") is not None: st += f'opacity:{d["opacity"]};'
        at = ""
        if d.get("motion"): at += f' data-motion="{esc(d["motion"])}"'
        if d.get("kf"): at += f' data-kf="{esc(json.dumps(d["kf"]))}"'
        if d.get("dur"): at += f' data-dur="{d["dur"]}"'
        out.append(f'<div class="decor {esc(d.get("kind","ring"))}" style="{st}"{at}></div>')
    return "".join(out)

def chrome(i, total, s, deck, body, cls=""):
    foot_l = esc(s.get("foot", deck.get("footer", "")))
    foot_r = esc(s.get("foot_right", deck.get("footer_right", ", ".join(a.split()[-1] for a in deck.get("authors", [])))))
    active = " active" if i == 0 else ""
    cls = f"lay-{cls}" if cls else ""
    return (f'<section class="slide {cls}{active}">{amb_html(s, deck)}{decor_html(s)}'
            f'<div class="head"><span class="tag">{rich(s.get("tag", deck.get("tag","")))}</span><span>{i+1:02d} / {total:02d}</span></div>'
            f'<div class="body">{body}</div><div class="foot"><span>{foot_l}</span><span>{foot_r}</span></div></section>')

# ----------------------------------------------------------------- layouts
def L_cover(s, deck):
    meta = "".join(f"<div><b>{rich(k)}</b>{rich(v)}</div>" for k, v in s.get("meta", []))
    authors = deck.get("authors", [])
    if authors:
        meta += f'<div><b>Presented by</b>{rich(", ".join(authors))}</div>'
    left = (f'<div class="eyebrow rise" style="--d:0">{rich(s.get("eyebrow",""))}</div>'
            f'<h1 class="kin rise" style="--d:1">{kinetic(s["title"])}</h1><div class="meta rise" style="--d:2">{meta}</div>'
            f'{blocks(s.get("left"), 3)}')
    right = blocks(s.get("right"), 2)
    return f'<div class="cover-body"><div class="left">{left}</div><div class="right">{right}</div></div>', "cover"

def L_flow(s, deck):
    parts = [title_html(s), blocks(s.get("blocks"), 1)]
    if s.get("columns"):
        cols = "".join(f"<div>{''.join(render_block(b) for b in c)}</div>" for c in s["columns"])
        parts.append(f'<div class="bt rise" style="--d:4;grid-template-columns:repeat({len(s["columns"])},1fr)">{cols}</div>')
    return "".join(parts), "flow"

def L_split(s, deck):
    cols = s.get("cols", "1fr 1fr")
    left = blocks(s.get("left"), 1)
    right = blocks(s.get("right"), 2)
    strip = f'<div class="rise" style="--d:5">{render_block({"type":"strip","items":s["strip"]})}</div>' if s.get("strip") else ""
    mid = " mid" if s.get("center") else ""
    return (f'{title_html(s)}<div class="lay{mid}" style="--cols:{cols}"><div class="col">{left}</div><div class="col">{right}</div></div>{strip}'), "split"

def L_pipeline(s, deck):
    pipe = blocks([{"type": "steps", "style": "apipe", "items": s["steps"]}], 1)
    low = "".join(f'<div class="rise" style="--d:{2+i}">{render_block(b)}</div>' for i, b in enumerate(s.get("cards", [])))
    cols = s.get("cols", " ".join(["1fr"] * len(s.get("cards", [1]))))
    return f'{title_html(s)}{pipe}<div class="low" style="--cols:{cols}">{low}</div>', "pipeline"

def L_cards(s, deck):
    lead = f'<p class="lead" style="max-width:400px">{rich(s["lead"])}</p>' if s.get("lead") else ""
    top = f'<div class="top2 free rise" style="--d:0;margin-bottom:24px">{title_html({**s,"title":s["title"]}).replace(" rise"," ").replace("--d:0","")}{lead}</div>' if lead else title_html(s)
    extra = blocks(s.get("blocks"), 3)
    return f'{top}<div class="rise" style="--d:1;margin-top:{0 if lead else 24}px">{b_cards({"items":s["cards"],"cols":s.get("cols",3)})}</div>{extra}', "cards"

def L_stats(s, deck):
    lead = f'<p class="lead rise" style="--d:1;max-width:560px;margin:12px 0 28px">{rich(s["lead"])}</p>' if s.get("lead") else '<div style="height:28px"></div>'
    return f'{title_html(s)}{lead}<div class="rise" style="--d:2">{b_stats({"items":s["items"]})}</div>{blocks(s.get("blocks"),3)}', "stats"

def L_compare(s, deck):
    formula = ""
    if s.get("formula"):
        parts = []
        for i, f in enumerate(s["formula"]):
            if i:
                parts.append(ic("x" if f.get("op") == "x" else "equal", 24, extra=' class="op"'))
            parts.append(f'<div class="tile{" out" if f.get("out") else ""}">{ico(f["icon"], size=20)}{rich(f["t"])}</div>')
        formula = f'<div class="formula">{"".join(parts)}</div>'
    top = f'<div class="top5 rise" style="--d:0">{title_html({**s}).replace(" rise"," ").replace("--d:0","")}{formula}</div>'
    cap = f'<p class="cap rise" style="--d:3;margin-top:16px">{rich(s.get("cap",""))}</p>' if s.get("cap") else ""
    return f'{top}<div class="rise" style="--d:1">{b_firms({"items":s["items"],"out_label":s.get("out_label","Result")})}</div>{cap}', "compare"

def L_chart(s, deck):
    left = blocks(s.get("left"), 1)
    return (f'{title_html(s)}<div class="lay" style="--cols:{s.get("cols","1fr 520px")}"><div class="col">{left}</div>'
            f'<div class="col rise" style="--d:2">{b_curve(s["chart"])}</div></div>{blocks(s.get("blocks"),3)}'), "chart"

def L_closing(s, deck):
    authors = deck.get("authors", [])
    by = '<div class="by rise" style="--d:2"><div><small>Presented by</small>' + esc(authors[0]) + "</div>" + "".join(f"<div><small>&nbsp;</small>{esc(a)}</div>" for a in authors[1:]) + "</div>" if authors else ""
    takes = "".join(f'<div class="card take rise" style="--d:{1+i}">{ico(t.get("icon","check"), t.get("acc"))}<div><h3>{rich(t["title"])}</h3><p>{rich(t.get("t",""))}</p></div></div>' for i, t in enumerate(s.get("takeaways", [])))
    return (f'<div class="closing"><div><div class="eyebrow rise" style="--d:0">{rich(s.get("eyebrow","Conclusion"))}</div>'
            f'<h1 class="kin rise" style="--d:1">{kinetic(s["title"])}</h1>{by}</div><div class="takes">{takes}</div></div>'), "closing"

def L_html(s, deck):
    return s["html"], "raw"

LAYOUTS = {k[2:]: v for k, v in globals().items() if k.startswith("L_")}

# ----------------------------------------------------------------- pages
def read(p): return Path(p).read_text(encoding="utf-8")

def head_html(deck, slug, css_href="../engine/theme.css"):
    acc = deck.get("accent")
    accv = f'<style>:root{{--acc:{acc};--acc-soft:{acc}18}}</style>' if acc else ""
    return (f'<!DOCTYPE html><html lang="{deck.get("lang","en")}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(deck["title"])}</title><meta name="description" content="{esc(deck.get("subtitle",""))}">'
            f'<link rel="preload" href="../fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="{css_href}">{accv}</head><body>')

def known_icons():
    return set(re.findall(r"export const (\w+)", read(ASSETS / "vendor" / "icons.js")))

def check_icons(slug, h):
    names = set(re.findall(r'data-i="(\w+)"', h))
    for m in re.findall(r'data-morph="([^"]+)"', h):
        names |= set(m.split(","))
    bad = sorted(names - known_icons())
    if bad:
        raise ValueError(f"{slug}: unknown icon(s) {bad}. Add with: python tools/addicons.py <lucide-name>  (kebab-case, e.g. chart-pie)")

def render_deck(slug, deck):
    slides = deck["slides"]
    total = len(slides)
    secs = []
    for i, s in enumerate(slides):
        lay = s.get("layout", "split")
        if lay not in LAYOUTS:
            raise ValueError(f"{slug}: slide {i+1}: unknown layout {lay!r}; known: {', '.join(sorted(LAYOUTS))}")
        try:
            body, cls = LAYOUTS[lay](s, deck)
        except KeyError as e:
            raise ValueError(f"{slug}: slide {i+1} ({lay}): missing field {e}") from None
        secs.append(chrome(i, total, s, deck, body, cls))
    pdf = deck.get("pdf") or f"{slug}.pdf"
    exp = ""
    if (DECKS / slug / pdf).exists():
        exp = f'<a class="export" id="exp" href="{esc(pdf)}" download>{ic("download")}<span>Download PDF</span></a>'
    ui = (f'<div class="ui"><button class="nav" id="prev" aria-label="Previous slide">{ic("arrowLeft")}</button><div class="dots" id="dots"></div>'
          f'<button class="nav" id="next" aria-label="Next slide">{ic("arrowRight")}</button></div>')
    cfg = json.dumps(deck.get("motion", {}))
    plug = '<script type="module" src="plugin.js"></script>' if (DECKS / slug / "plugin.js").exists() else ""
    return (head_html(deck, slug) + exp + f'<div id="viewport"><main id="deck">{"".join(secs)}</main></div>' + ui +
            f'<script type="application/json" id="deck-config">{cfg}</script>'
            '<script type="module" src="../engine/motion.js"></script>' + plug + '<script src="../engine/remote.js" defer></script></body></html>')

def slide_titles_from_html(h):
    out = []
    for sec in re.split(r'<section class="slide', h)[1:]:
        m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", sec, re.S)
        t = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
        t = re.sub(r"^\s*\d+\s+", "", re.sub(r"\s+", " ", html.unescape(t)).strip())
        out.append(t)
    return out

def inject_legacy(h):
    h = h.replace("</body>", '<script src="../engine/remote.js" defer></script></body>')
    h = h.replace("</head>", "<style>.thumb .ui,.thumb .export,.thumb .rbtn,.thumb .rpop{display:none!important}</style>"
                  "<script>if(/[?&]thumb/.test(location.search))document.documentElement.classList.add('thumb')</script></head>", 1)
    return h

def build(quiet=False):
    t0 = time.time()
    tmp = ROOT / "dist.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "engine").mkdir(parents=True)
    shutil.copytree(ASSETS / "vendor", tmp / "vendor")
    shutil.copytree(ASSETS / "fonts", tmp / "fonts")
    (tmp / "engine" / "theme.css").write_text(read(ENGINE / "theme.base.css") + "\n" + read(ENGINE / "theme.add.css"), encoding="utf-8")
    for f in ("motion.js", "remote.js"):
        shutil.copy(ENGINE / f, tmp / "engine" / f)

    index = []
    for d in sorted(DECKS.iterdir()):
        if not (d / "deck.json").exists():
            continue
        slug = d.name
        deck = json.loads(read(d / "deck.json"))
        out = tmp / slug
        out.mkdir()
        if deck.get("legacy"):
            h = read(d / "legacy.html")
            titles = slide_titles_from_html(h)
            (out / "index.html").write_text(inject_legacy(h), encoding="utf-8")
        else:
            h = render_deck(slug, deck)
            check_icons(slug, h)
            titles = slide_titles_from_html(h)
            (out / "index.html").write_text(h, encoding="utf-8")
        if (d / "plugin.js").exists():
            shutil.copy(d / "plugin.js", out / "plugin.js")
        pdf = deck.get("pdf") or f"{slug}.pdf"
        has_pdf = (d / pdf).exists()
        if has_pdf:
            shutil.copy(d / pdf, out / pdf)
        langs = sorted(p.name.split(".")[1] for p in d.glob("speech.*.md"))
        index.append({
            "slug": slug, "title": deck["title"], "subtitle": deck.get("subtitle", ""), "authors": deck.get("authors", []),
            "date": deck.get("date", ""), "tags": deck.get("tags", []), "slides": len(titles), "titles": titles,
            "pdf": f"{slug}/{pdf}" if has_pdf else "", "langs": langs, "minutes": deck.get("minutes", 0),
            "order": deck.get("order", 0), "hidden": bool(deck.get("hidden")),
        })
    for r in json.loads(read(ROOT / "redirects.json")) if (ROOT / "redirects.json").exists() else []:
        p = tmp / r["from"].strip("/")
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={r["to"]}"><script>location.replace("{r["to"]}"+location.hash)</script>', encoding="utf-8")
    index.sort(key=lambda x: (x["order"], x["date"]), reverse=True)
    (tmp / "decks.json").write_text(json.dumps([i for i in index if not i["hidden"]], ensure_ascii=False, indent=1), encoding="utf-8")
    (tmp / "index.html").write_text(read(ENGINE / "gallery.html"), encoding="utf-8")
    (tmp / "admin").mkdir()
    (tmp / "admin" / "index.html").write_text(read(ENGINE / "admin.html"), encoding="utf-8")

    old = ROOT / "dist.old"
    if old.exists():
        shutil.rmtree(old)
    if DIST.exists():
        DIST.rename(old)
    tmp.rename(DIST)
    if old.exists():
        shutil.rmtree(old)
    if not quiet:
        print(f"built {len(index)} deck(s) in {time.time()-t0:.2f}s -> {DIST}")
    return index

if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print("BUILD FAILED:", e, file=sys.stderr)
        sys.exit(1)
