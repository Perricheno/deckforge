#!/usr/bin/env python3
"""deckforge server: static site (never cached) + presenter remote API (PIN, SSE) + auto rebuild.

  python tools/serve.py --port 8191 [--auto-pdf]
  python tools/setpin.py 123456            change the presenter PIN

API (all under /api):
  GET  /events/<slug>?role=viewer|admin&token=   SSE: `state` events {slide, live, viewers, ts}
  GET  /state/<slug>                             current slide (public)
  POST /login        {pin} -> {token}            rate limited
  POST /slide/<slug> {slide}|{delta}  (Bearer)   moves every viewer
  GET  /speech/<slug>?lang=en        (Bearer)    speaker notes (Markdown), never served as a static file
"""
import argparse, base64, hashlib, hmac, json, mimetypes, os, queue, secrets, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import importlib
import build as builder  # noqa: E402
_bp = ROOT / "tools" / "build.py"
_bm = [_bp.stat().st_mtime]

DATA, DIST, DECKS = ROOT / "data", ROOT / "dist", ROOT / "decks"
DATA.mkdir(exist_ok=True)
PIN_LEN = 6
TOKEN_TTL = 3 * 24 * 3600
NO_CACHE = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache", "Expires": "0",
    "CDN-Cache-Control": "no-store", "Cloudflare-CDN-Cache-Control": "no-store",
}

# HTML and deck metadata need to update immediately.  Large immutable assets
# should not be downloaded again whenever someone returns to the gallery.
ASSET_CACHE = {
    "Cache-Control": "public, max-age=604800, immutable",
    "CDN-Cache-Control": "public, max-age=604800, immutable",
    "Cloudflare-CDN-Cache-Control": "public, max-age=604800, immutable",
}
SHORT_CACHE = {
    "Cache-Control": "public, max-age=300",
    "CDN-Cache-Control": "public, max-age=300",
    "Cloudflare-CDN-Cache-Control": "public, max-age=300",
}

# ------------------------------------------------------------------ auth
def _secret():
    f = DATA / "secret.key"
    if not f.exists():
        f.write_text(secrets.token_hex(32)); f.chmod(0o600)
    return f.read_text().strip().encode()

def set_pin(pin):
    if not (pin.isdigit() and len(pin) == PIN_LEN):
        raise ValueError(f"PIN must be exactly {PIN_LEN} digits")
    salt = secrets.token_hex(8)
    (DATA / "auth.json").write_text(json.dumps({"salt": salt, "hash": hashlib.sha256((salt + pin).encode()).hexdigest()}))
    (DATA / "auth.json").chmod(0o600)

def check_pin(pin):
    f = DATA / "auth.json"
    if not f.exists():
        return False
    a = json.loads(f.read_text())
    return hmac.compare_digest(hashlib.sha256((a["salt"] + pin).encode()).hexdigest(), a["hash"])

def make_token():
    body = base64.urlsafe_b64encode(json.dumps({"exp": int(time.time()) + TOKEN_TTL}).encode()).decode().rstrip("=")
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"

def verify_token(tok):
    try:
        body, sig = tok.split(".")
        if not hmac.compare_digest(hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest(), sig):
            return False
        return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))["exp"] > time.time()
    except Exception:
        return False

_attempts, _alock = {}, threading.Lock()
def throttle(ip, ok=None):
    """5 tries / minute, 10 failures -> 10 minute lock. Returns seconds to wait or 0."""
    now = time.time()
    with _alock:
        rec = _attempts.setdefault(ip, {"t": [], "fail": [], "lock": 0})
        if rec["lock"] > now:
            return int(rec["lock"] - now) + 1
        rec["t"] = [x for x in rec["t"] if now - x < 60]
        rec["fail"] = [x for x in rec["fail"] if now - x < 600]
        if ok is None:
            if len(rec["t"]) >= 5:
                return int(60 - (now - rec["t"][0])) + 1
            rec["t"].append(now)
            return 0
        if ok is False:
            rec["fail"].append(now)
            if len(rec["fail"]) >= 10:
                rec["lock"] = now + 600
        else:
            rec["fail"].clear()
        return 0

# ------------------------------------------------------------------ live state
STATE, CLIENTS, LOCK = {}, {}, threading.Lock()
SF = DATA / "state.json"
if SF.exists():
    try: STATE = json.loads(SF.read_text())
    except Exception: STATE = {}

def snapshot(slug):
    with LOCK:
        cl = CLIENTS.get(slug, set())
        return {"slide": STATE.get(slug, {}).get("slide", 0), "live": any(c.role == "admin" for c in cl),
                "viewers": sum(1 for c in cl if c.role == "viewer"), "ts": STATE.get(slug, {}).get("ts", 0)}

def broadcast(slug):
    snap = snapshot(slug)
    with LOCK:
        for c in list(CLIENTS.get(slug, [])):
            c.q.put(snap)

class Client:
    def __init__(self, role): self.q, self.role = queue.Queue(), role

def deck_count(slug):
    try:
        for d in json.loads((DIST / "decks.json").read_text()):
            if d["slug"] == slug: return d["slides"]
    except Exception: pass
    return 0

# ------------------------------------------------------------------ build / pdf
_build = {"at": 0, "checked": 0, "err": "", "lock": threading.Lock()}
AUTO_PDF, PORT = False, 8191
_pdf_q, _pdf_busy = queue.Queue(), set()

def newest():
    m = 0
    for base in (DECKS, ROOT / "engine", ROOT / "assets"):
        for p in base.rglob("*"):
            if p.is_file() and not p.name.endswith(".pdf"):
                m = max(m, p.stat().st_mtime)
    for p in (ROOT / "tools" / "build.py", ROOT / "redirects.json"):
        if p.exists(): m = max(m, p.stat().st_mtime)
    pdfs = [p.stat().st_mtime for p in DECKS.rglob("*.pdf")]
    return max(m, max(pdfs) if pdfs else 0)

def maybe_build(force=False):
    now = time.time()
    if not force and now - _build["checked"] < .6:
        return
    _build["checked"] = now
    if not force and DIST.exists() and newest() <= _build["at"]:
        return
    with _build["lock"]:
        if not force and DIST.exists() and newest() <= _build["at"]:
            return
        stamp = time.time()
        try:
            if _bp.stat().st_mtime != _bm[0]:      # edited build.py is picked up without a restart
                importlib.reload(builder); _bm[0] = _bp.stat().st_mtime
            builder.build(quiet=True)
            _build["err"] = ""
            print(time.strftime("%H:%M:%S"), "rebuilt", flush=True)
        except Exception as e:
            _build["err"] = f"{type(e).__name__}: {e}"
            print("BUILD ERROR:", _build["err"], file=sys.stderr, flush=True)
        _build["at"] = stamp
    if AUTO_PDF:
        queue_pdfs()

def queue_pdfs():
    for d in DECKS.iterdir():
        if not (d / "deck.json").exists(): continue
        try: deck = json.loads((d / "deck.json").read_text())
        except Exception: continue
        pdf = d / (deck.get("pdf") or f"{d.name}.pdf")
        src = max([(d / n).stat().st_mtime for n in ("deck.json", "legacy.html", "plugin.js") if (d / n).exists()] or [0])
        if (not pdf.exists() or pdf.stat().st_mtime < src) and d.name not in _pdf_busy:
            _pdf_busy.add(d.name); _pdf_q.put(d.name)

def pdf_worker():
    py = ROOT / ".venv" / "bin" / "python"
    while True:
        slug = _pdf_q.get()
        try:
            r = subprocess.run([str(py if py.exists() else sys.executable), str(ROOT / "tools" / "pdf.py"), slug, "--port", str(PORT)],
                               capture_output=True, text=True, timeout=180)
            print("pdf", slug, "ok" if r.returncode == 0 else "FAILED " + r.stderr[-300:], flush=True)
        except Exception as e:
            print("pdf", slug, "error", e, flush=True)
        finally:
            _pdf_busy.discard(slug)

# ------------------------------------------------------------------ http
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "deckforge"

    def log_message(self, *a): pass

    def ip(self):
        return self.headers.get("CF-Connecting-IP") or (self.headers.get("X-Forwarded-For", "").split(",")[0].strip()) or self.client_address[0]

    def send(self, code, body=b"", ctype="text/plain; charset=utf-8", extra=None):
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in {**NO_CACHE, **(extra or {})}.items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def json(self, code, obj, extra=None):
        self.send(code, json.dumps(obj), "application/json; charset=utf-8", extra)

    def authed(self, q=None):
        h = self.headers.get("Authorization", "")
        tok = h[7:] if h.startswith("Bearer ") else (q or {}).get("token", [""])[0]
        return verify_token(tok)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try: return json.loads(self.rfile.read(n) or b"{}")
        except Exception: return {}

    # -------- routing
    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query); p = unquote(u.path)
        if p.startswith("/api/"):
            return self.api_get(p[5:], q)
        maybe_build()
        self.static(p)

    def do_POST(self):
        u = urlparse(self.path); p = unquote(u.path)
        if not p.startswith("/api/"): return self.send(404, "not found")
        self.api_post(p[5:], parse_qs(u.query))

    def static(self, p):
        if _build["err"] and not DIST.exists():
            return self.send(500, "Build failed:\n" + _build["err"])
        rel = p.lstrip("/")
        f = (DIST / rel).resolve()
        if DIST.resolve() not in f.parents and f != DIST.resolve():
            return self.send(403, "forbidden")
        if f.is_dir():
            if not p.endswith("/"):
                return self.send(301, "", extra={"Location": p + "/"})
            f = f / "index.html"
        if not f.exists():
            return self.send(404, "Not found")
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if f.suffix in (".html", ".css", ".js", ".json", ".md"): ctype += "; charset=utf-8"
        if f.suffix == ".js": ctype = "text/javascript; charset=utf-8"
        # Keep navigational documents fresh, but cache assets.  This avoids
        # repeated 10–20 MB PDF/font/image transfers and markedly reduces
        # mobile CPU/network pressure when opening the site again.
        if f.suffix.lower() in (".woff", ".woff2", ".png", ".jpg", ".jpeg", ".webp", ".svg"):
            extra = ASSET_CACHE
        elif f.suffix.lower() in (".css", ".js", ".pdf"):
            extra = SHORT_CACHE
        else:
            extra = None
        self.send(200, f.read_bytes(), ctype, extra=extra)

    def api_get(self, p, q):
        parts = p.split("/")
        if parts[0] == "whoami": return self.json(200 if self.authed(q) else 401, {"ok": self.authed(q)})
        if parts[0] == "ping": return self.json(200, {"ok": True, "build_error": _build["err"]})
        if parts[0] == "state" and len(parts) > 1: return self.json(200, snapshot(parts[1]))
        if parts[0] == "events" and len(parts) > 1: return self.sse(parts[1], q)
        if parts[0] == "speech" and len(parts) > 1:
            if not self.authed(q): return self.json(401, {"error": "auth"})
            slug = parts[1]; d = DECKS / slug
            if not d.is_dir() or "/" in slug or ".." in slug: return self.json(404, {"error": "no deck"})
            langs = sorted(f.name.split(".")[1] for f in d.glob("speech.*.md"))
            lang = (q.get("lang", [""])[0] or (langs[0] if langs else ""))
            md = (d / f"speech.{lang}.md").read_text(encoding="utf-8") if lang in langs else ""
            return self.json(200, {"langs": langs, "lang": lang, "md": md})
        self.json(404, {"error": "unknown endpoint"})

    def api_post(self, p, q):
        parts = p.split("/")
        if parts[0] == "login":
            ip = self.ip(); wait = throttle(ip)
            if wait: return self.json(429, {"error": "too many attempts", "retry": wait}, {"Retry-After": str(wait)})
            pin = str(self.body().get("pin", ""))
            ok = check_pin(pin)
            throttle(ip, ok)
            if not ok: return self.json(401, {"error": "wrong pin"})
            return self.json(200, {"token": make_token(), "ttl": TOKEN_TTL, "len": PIN_LEN})
        if parts[0] == "slide" and len(parts) > 1:
            if not self.authed(): return self.json(401, {"error": "auth"})
            slug, b = parts[1], self.body()
            n = deck_count(slug)
            if not n: return self.json(404, {"error": "no deck"})
            cur = STATE.get(slug, {}).get("slide", 0)
            tgt = int(b["slide"]) if "slide" in b else cur + int(b.get("delta", 0))
            tgt = max(0, min(n - 1, tgt))
            with LOCK:
                STATE[slug] = {"slide": tgt, "ts": int(time.time() * 1000)}
                SF.write_text(json.dumps(STATE))
            broadcast(slug)
            return self.json(200, snapshot(slug))
        self.json(404, {"error": "unknown endpoint"})

    def sse(self, slug, q):
        role = q.get("role", ["viewer"])[0]
        if role == "admin" and not self.authed(q):
            return self.json(401, {"error": "auth"})
        c = Client("admin" if role == "admin" else "viewer")
        with LOCK: CLIENTS.setdefault(slug, set()).add(c)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "keep-alive")
            for k in ("CDN-Cache-Control", "Cloudflare-CDN-Cache-Control"): self.send_header(k, "no-store")
            self.end_headers()
            self.wfile.write(b"retry: 2000\n\n")
            broadcast(slug)
            while True:
                try:
                    snap = c.q.get(timeout=15)
                    self.wfile.write(b"event: state\ndata: " + json.dumps(snap).encode() + b"\n\n")
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with LOCK: CLIENTS.get(slug, set()).discard(c)
            broadcast(slug)

class Srv(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8191)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--auto-pdf", action="store_true")
    a = ap.parse_args()
    AUTO_PDF, PORT = a.auto_pdf, a.port
    if not (DATA / "auth.json").exists():
        pin = "".join(secrets.choice("0123456789") for _ in range(PIN_LEN))
        set_pin(pin)
        print(f"first run: presenter PIN is {pin} (change it with: python tools/setpin.py <6 digits>)", flush=True)
    maybe_build(force=True)
    if AUTO_PDF:
        threading.Thread(target=pdf_worker, daemon=True).start()
        queue_pdfs()
    print(f"deckforge serving {DIST} on http://{a.host}:{a.port}", flush=True)
    Srv((a.host, a.port), H).serve_forever()
