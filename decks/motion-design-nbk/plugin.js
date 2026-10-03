// Hand-written visual for the NBK deck: a self-playing simulation of an economy reacting to a demand shock.
// Nothing here is a template block: it is plain canvas code, which is the point of the "custom" layer.
const DM = window.DeckMotion;

DM.custom('economy', (el, api) => {
  const W = 1180, H = 520, DPR = 2, N = 126, STEP = 0.115;            // N model steps, STEP seconds per step
  const cv = document.createElement('canvas');
  cv.width = W * DPR; cv.height = H * DPR; cv.style.cssText = `width:${W}px;height:${H}px;display:block`;
  el.appendChild(cv);
  const g = cv.getContext('2d'); g.scale(DPR, DPR);
  const cs = getComputedStyle(el), C = n => cs.getPropertyValue(n).trim();

  // ---- the stylised model (illustrative units): demand shock at step 34, bank reacts from step 68
  const sim = []; {
    let r = 8, i = 8, y = 0, p = 5, s = 0;
    for (let k = 0; k < N; k++) {
      if (k === 34) s = 3;
      if (k >= 68) { const tgt = Math.min(16, Math.max(2, 8 + 2.4 * (p - 5) + 0.9 * y)); r += 0.085 * (tgt - r); }
      i += 0.09 * (r - i);
      y = 0.86 * y - 0.10 * (i - 8) + 0.14 * s;
      p = 0.94 * p + 0.06 * (5 + 1.3 * y);
      sim.push({ r, i, y, p });
    }
  }
  const PH = [
    { from: 0,   t: 'Calm',                       d: 'Spending, credit and prices are in balance. Inflation sits at the target.' },
    { from: 34,  t: 'Demand shock',               d: 'A burst of demand: households and firms spend more, so prices start to rise.' },
    { from: 68,  t: 'The bank raises the rate',   d: 'The National Bank lifts the base rate. Loans get pricier, so credit and spending cool.' },
    { from: 108, t: 'Prices come back',           d: 'Demand eases and inflation returns to the target.' },
  ];
  const NOTES = [
    { k: 34,  t: 'Demand shock',        y: 'up' },
    { k: 68,  t: 'Rate decision',       y: 'up' },
    { k: 110, t: 'Back near target',    y: 'dn' },
  ];

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = p => .5 - .5 * Math.cos(Math.PI * clamp(p));
  const rr = (x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
  const txt = (s, x, y, size, weight, col, align = 'left', ls = 0) => { g.font = `${weight} ${size}px Inter, sans-serif`; g.fillStyle = col; g.textAlign = align; g.letterSpacing = ls + 'px'; g.fillText(s, x, y); };

  // ---- diagram geometry: a clockwise loop  bank -> banks -> households -> shops -> (measured) -> bank
  const NODE = { cb: [20, 150, 240, 96], bk: [380, 150, 240, 96], hh: [380, 390, 240, 96], sh: [20, 390, 240, 96] };
  const mid = n => [NODE[n][0] + NODE[n][2] / 2, NODE[n][1] + NODE[n][3] / 2];
  const edge = (a, b) => [mid(a), mid(b)];
  const EDGES = {
    rate:   { ...{ from: 'cb', to: 'bk' }, col: 'acc',  label: 'rate signal' },
    credit: { ...{ from: 'bk', to: 'hh' }, col: 'acc',  label: 'credit' },
    spend:  { ...{ from: 'hh', to: 'sh' }, col: 'ink',  label: 'spending' },
    price:  { ...{ from: 'sh', to: 'cb' }, col: 'faint', label: 'inflation measured' },
  };

  function particles(a, b, t, n, speed, alpha, col, size) {
    const nmax = 26;
    for (let k = 0; k < nmax; k++) {
      const vis = clamp(n - k); if (!vis) continue;
      const q = ((t * speed + k / nmax) % 1);
      const x = a[0] + (b[0] - a[0]) * q, y = a[1] + (b[1] - a[1]) * q;
      g.globalAlpha = alpha * vis * Math.sin(Math.PI * Math.min(1, q * 1.1)); g.fillStyle = col;
      g.beginPath(); g.arc(x, y, size, 0, 7); g.fill();
    }
    g.globalAlpha = 1;
  }

  function frame(t, dt, st) {
    const k = clamp(st / STEP, 0, N - 0.001), ki = Math.floor(k), s = sim[ki];
    const ink = C('--ink'), acc = C('--acc'), mute = C('--mute'), faint = C('--faint'), line = C('--line'), card = C('--card'), tint = C('--tint'), on = C('--on');
    g.clearRect(0, 0, W, H);

    // ---- phase stepper + caption
    const ph = PH.reduce((a, p, n) => (ki >= p.from ? n : a), 0);
    const colW = W / PH.length;
    PH.forEach((p, n) => {
      const x = n * colW, active = n === ph, done = n < ph;
      g.fillStyle = active ? acc : (done ? ink : line); g.beginPath(); g.arc(x + 14, 26, 14, 0, 7); g.fill();
      txt(String(n + 1), x + 14, 31.5, 14, 700, active || done ? on : mute, 'center');
      txt(p.t, x + 38, 31.5, 17, active ? 700 : 500, active ? ink : (done ? mute : faint));
      const end = n + 1 < PH.length ? PH[n + 1].from : N, pr = clamp((k - p.from) / (end - p.from));
      g.fillStyle = line; g.fillRect(x, 54, colW - 24, 2);
      g.fillStyle = active ? acc : ink; g.fillRect(x, 54, (colW - 24) * (done ? 1 : active ? pr : 0), 2);
    });
    const cap = PH[ph].d, capA = clamp((k - PH[ph].from) / 3);
    g.globalAlpha = capA; txt(cap, 0, 100, 19, 400, ink); g.globalAlpha = 1;

    // ---- flows (particle density follows the model)
    const credit = clamp(1.25 - (s.i - 8) / 9, .12, 1.6), spend = clamp(1 + s.y * .32, .15, 2.1);
    const ratePow = clamp(s.r / 16, .1, 1);
    const [r1a, r1b] = edge('cb', 'bk'), [r2a, r2b] = edge('bk', 'hh'), [r3a, r3b] = edge('hh', 'sh'), [r4a, r4b] = edge('sh', 'cb');
    g.lineCap = 'round';
    for (const [a, b, w] of [[r1a, r1b, 1 + ratePow * 5], [r2a, r2b, 1.2], [r3a, r3b, 1.2], [r4a, r4b, 1.2]]) {
      g.strokeStyle = line; g.lineWidth = w; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    }
    particles(r1a, r1b, t, .35 + ratePow * 2.2, .18, .9, acc, 3.4);
    particles(r2a, r2b, t, credit * 7, .16, .9, acc, 3.2);
    particles(r3a, r3b, t, spend * 7, .17, .9, ink, 3.2);
    particles(r4a, r4b, t, .9, .12, .55, faint, 2.6);
    // edge labels
    txt('RATE SIGNAL', (r1a[0] + r1b[0]) / 2, r1a[1] - 16, 11, 600, faint, 'center', 1.4);
    g.save(); g.translate(r2a[0] + 18, (r2a[1] + r2b[1]) / 2); g.rotate(Math.PI / 2); txt('CREDIT', 0, 0, 11, 600, faint, 'center', 1.4); g.restore();
    txt('SPENDING', (r3a[0] + r3b[0]) / 2, r3a[1] + 30, 11, 600, faint, 'center', 1.4);
    g.save(); g.translate(r4a[0] - 18, (r4a[1] + r4b[1]) / 2); g.rotate(-Math.PI / 2); txt('PRICES MEASURED', 0, 0, 11, 600, faint, 'center', 1.4); g.restore();

    // ---- nodes with live values
    const node = (n, title, value, unit, hot) => {
      const [x, y, w, h] = NODE[n]; rr(x, y, w, h, 16); g.fillStyle = card; g.fill(); g.lineWidth = hot ? 2 : 1.4; g.strokeStyle = hot ? acc : line; g.stroke();
      txt(title.toUpperCase(), x + 18, y + 28, 11, 600, mute, 'left', 1.3);
      txt(value, x + 18, y + 70, 36, 600, ink, 'left', -1); const vw = g.measureText(value).width; txt(unit, x + 22 + vw, y + 70, 15, 500, faint);
    };
    node('cb', 'National Bank · rate', s.r.toFixed(1), '%', ph === 2);
    node('bk', 'Banks · loan rate', s.i.toFixed(1), '%', false);
    node('hh', 'Households · demand', String(Math.round(100 + s.y * 14)), 'index', ph === 1);
    // shops: thermometer of inflation vs target
    { const [x, y, w, h] = NODE.sh; rr(x, y, w, h, 16); g.fillStyle = card; g.fill(); g.lineWidth = s.p > 6 ? 2 : 1.4; g.strokeStyle = s.p > 6 ? acc : line; g.stroke();
      txt('SHOPS · INFLATION', x + 18, y + 28, 11, 600, mute, 'left', 1.3);
      txt(s.p.toFixed(1), x + 18, y + 70, 36, 600, ink, 'left', -1); const vw = g.measureText(s.p.toFixed(1)).width; txt('%', x + 22 + vw, y + 70, 15, 500, faint);
      const tx = x + w - 62, tw = 38, th = 12; rr(tx, y + 58, tw * 1.0 + 16, th, 6); g.fillStyle = tint; g.fill();
      const fillW = clamp(s.p / 12) * (tw + 16); rr(tx, y + 58, Math.max(10, fillW), th, 6); g.fillStyle = s.p > 6 ? acc : ink; g.fill();
      const tgtX = tx + clamp(5 / 12) * (tw + 16); g.strokeStyle = ink; g.lineWidth = 1.6; g.beginPath(); g.moveTo(tgtX, y + 52); g.lineTo(tgtX, y + 76); g.stroke();
      txt('target', tgtX, y + 90, 10, 600, faint, 'center'); }

    // ---- chart
    const cx0 = 720, cx1 = 1180, cy0 = 160, cy1 = 452, X = n => cx0 + (n / (N - 1)) * (cx1 - cx0), Y = v => cy1 - (v / 16) * (cy1 - cy0);
    g.fillStyle = tint; g.fillRect(cx0, Y(6), cx1 - cx0, Y(4) - Y(6));
    g.strokeStyle = line; g.lineWidth = 1; [4, 8, 12, 16].forEach(v => { g.beginPath(); g.moveTo(cx0, Y(v)); g.lineTo(cx1, Y(v)); g.stroke(); txt(String(v), cx0 - 10, Y(v) + 4, 11, 500, faint, 'right'); });
    g.setLineDash([3, 5]); g.strokeStyle = ink; g.beginPath(); g.moveTo(cx0, Y(5)); g.lineTo(cx1, Y(5)); g.stroke(); g.setLineDash([]);
    txt('TARGET', cx1, Y(5) - 7, 10, 600, faint, 'right', 1.2);
    // legend
    [['Inflation', ink, 3], ['Base rate', acc, 3], ['Loan rate', faint, 2]].forEach(([n, c, w], q) => { const lx = cx0 + q * 104; g.strokeStyle = c; g.lineWidth = w; g.beginPath(); g.moveTo(lx, cy1 + 26); g.lineTo(lx + 18, cy1 + 26); g.stroke(); txt(n, lx + 24, cy1 + 30, 12, 500, mute); });
    const series = (key, col, w, dash) => { g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.beginPath(); for (let n = 0; n <= ki; n++) { n ? g.lineTo(X(n), Y(sim[n][key])) : g.moveTo(X(n), Y(sim[n][key])); } g.stroke(); g.setLineDash([]);
      const e = sim[ki]; g.fillStyle = col; g.beginPath(); g.arc(X(ki), Y(e[key]), w + 2.2, 0, 7); g.fill(); };
    series('i', faint, 2, [5, 4]); series('r', acc, 3); series('p', ink, 3.4);
    // notes appear when the cursor has passed them
    NOTES.forEach(nt => { if (ki < nt.k) return; const a = clamp((k - nt.k) / 2.5), x = X(nt.k), py = Y(sim[nt.k].p);
      g.globalAlpha = a; g.strokeStyle = faint; g.setLineDash([2, 4]); g.beginPath(); g.moveTo(x, cy0 - 6); g.lineTo(x, cy1); g.stroke(); g.setLineDash([]);
      g.font = '600 11px Inter, sans-serif'; const cw = g.measureText(nt.t).width + 22, bx = Math.min(x - 3, cx1 - cw); rr(bx, cy0 - 26, cw, 20, 10); g.fillStyle = ink; g.fill(); txt(nt.t, bx + 11, cy0 - 12, 11, 600, on); g.globalAlpha = 1; });
    txt('Stylised model, illustrative units', cx0, cy1 + 56, 11, 400, faint);
  }
  return frame;
});
