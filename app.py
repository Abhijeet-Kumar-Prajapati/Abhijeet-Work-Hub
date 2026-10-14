"""
Abhijeet Work Hub  -  app.py
=============================
One single software that holds every project in one place.

    Flask backend  +  one modern HTML frontend.

Run it:
    python app.py
Then open the printed URL.

SECURITY POSTURE
----------------
* session key is never committed - see hub_config.get_secret_key()
* binds to 127.0.0.1 by default, so it is not reachable from the network
* every response carries CSP, X-Frame-Options and friends
* mutating endpoints are rate limited per client
* the file reader is jailed inside WORKSPACE_ROOT and refuses to serve
  anything in public mode
* internal error text is never returned to the browser
* no absolute path or user name is ever sent to the frontend
"""

import json
import sqlite3
import logging
import subprocess
import sys
import time
import datetime
import re
import threading
from collections import defaultdict, deque
from pathlib import Path

# some portable / embedded Python builds do not put the script folder on
# sys.path, so add it explicitly to make the local import work everywhere
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, render_template, jsonify, request, abort

import hub_config as cfg

HERE = Path(__file__).resolve().parent
DATA_FILE = cfg.DATA_DIR / "projects.json"
HUB_DB = cfg.DATA_DIR / "hub.db"
BUILDER = HERE / "build_catalog.py"

SECRET_KEY, SECRET_SOURCE = cfg.get_secret_key()
WORKSPACE = Path(cfg.WORKSPACE_ROOT)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    JSON_SORT_KEYS=False,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    # pick up template edits without restarting the server
    TEMPLATES_AUTO_RELOAD=True,
)
app.json.ensure_ascii = False
app.json.sort_keys = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("hub")

# extensions the code browser is allowed to render as text
TEXT_EXT = {
    ".py", ".js", ".mjs", ".html", ".htm", ".css", ".kt", ".java",
    ".json", ".md", ".txt", ".xml", ".bat", ".ps1", ".pyw", ".yaml",
    ".yml", ".ini", ".cfg", ".csv", ".c", ".h", ".cpp", ".sql",
}
MAX_READ_BYTES = 400_000
MAX_LIST_ITEMS = 300

# neutral demo identities - example.com is reserved for documentation
DEMO_ACCOUNTS = [
    ("Demo User", "user1@example.com", 12500.0),
    ("Wallet",    "user2@example.com", 0.0),
    ("Alex",      "user3@example.com", 4200.0),
    ("Sam",       "user4@example.com", 3100.0),
]

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


# ============================================================ security bits
class RateLimiter:
    """Tiny in-memory sliding-window limiter. Good enough for a local tool."""

    def __init__(self, limit=30, window=60):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


limiter = RateLimiter(limit=40, window=60)


@app.after_request
def security_headers(resp):
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "media-src 'self' blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "object-src 'none'",
    )
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy",
                            "geolocation=(), microphone=(), camera=()")
    resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resp.headers.setdefault("X-Work-Hub-Mode", "public" if cfg.IS_PUBLIC else "local")
    return resp


@app.before_request
def guard():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        client = request.remote_addr or "local"
        if not limiter.allow(client):
            return jsonify({"ok": False, "error": "Too many requests - slow down"}), 429


def want_json():
    return request.accept_mimetypes.best == "application/json"


# ============================================================ catalogue
def clean_catalog(raw):
    """Strip anything unexpected before it reaches the browser."""
    out = {"meta": {}, "categories": []}
    if not isinstance(raw, dict):
        return out

    meta = raw.get("meta")
    if isinstance(meta, dict):
        out["meta"] = {
            k: v for k, v in meta.items()
            if k in ("app", "owner", "generated", "categories",
                     "projects", "files", "kb", "workspace_set")
        }

    cats = raw.get("categories")
    if isinstance(cats, list):
        for c in cats[:50]:
            if not isinstance(c, dict):
                continue
            color = c.get("color", "#6366f1")
            if not (isinstance(color, str) and HEX_RE.match(color)):
                color = "#6366f1"
            projs = []
            for p in (c.get("projects") or [])[:200]:
                if not isinstance(p, dict) or not p.get("id"):
                    continue
                projs.append({
                    "id": str(p["id"])[:60],
                    "title": str(p.get("title", ""))[:120],
                    "desc": str(p.get("desc", ""))[:600],
                    "tech": [str(t)[:30] for t in (p.get("tech") or [])][:12],
                    "features": [str(f)[:160] for f in (p.get("features") or [])][:20],
                    "exists": bool(p.get("exists")),
                    "files": int(p.get("files") or 0),
                    "kb": int(p.get("kb") or 0),
                    "date": str(p.get("date") or "")[:10],
                    "demo": p.get("demo"),
                    "entry": str(p.get("entry") or "")[:120],
                    "highlight": bool(p.get("highlight")),
                    "subpath": str(p.get("subpath") or "")[:400],
                })
            out["categories"].append({
                "id": str(c.get("id", ""))[:40],
                "title": str(c.get("title", ""))[:80],
                "color": color,
                "projects": projs,
            })
    return out


def load_catalog():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return clean_catalog(json.load(f))
    except (OSError, ValueError):
        log.warning("catalogue missing or invalid - run build_catalog.py")
        return {"meta": {}, "categories": []}


def find_project(pid):
    for cat in load_catalog()["categories"]:
        for p in cat["projects"]:
            if p["id"] == pid:
                p = dict(p)
                p["category"] = cat["title"]
                p["categoryId"] = cat["id"]
                return p
    return None


def resolve_in_workspace(user_path):
    """
    Turn a user supplied relative path into an absolute path that is
    guaranteed to sit inside WORKSPACE_ROOT.

    Rejects: absolute paths, drive letters, UNC paths, '..' traversal,
    null bytes, and symlinks that point outside the root.
    """
    if not cfg.is_safe_relpath(user_path):
        abort(400)

    root = WORKSPACE.resolve()
    try:
        target = (root / user_path).resolve()
        target.relative_to(root)          # raises if it escapes
    except (ValueError, OSError):
        abort(403)

    if not target.exists():
        abort(404)
    return target


# ============================================================ wallet demo
def db():
    conn = sqlite3.connect(HUB_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    cfg.DATA_DIR.mkdir(exist_ok=True)
    conn = db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE, balance REAL NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY, frm INTEGER NOT NULL,
                to_id INTEGER NOT NULL, amount REAL NOT NULL,
                note TEXT, ts TEXT NOT NULL);
            """
        )
        if not conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]:
            conn.executemany(
                "INSERT INTO accounts (name, email, balance) VALUES (?,?,?)", DEMO_ACCOUNTS)
            conn.commit()
    except sqlite3.Error as exc:
        log.error("db init failed: %s", exc)
    finally:
        conn.close()


# ============================================================ pages
@app.route("/")
def index():
    return render_template("index.html", catalog=load_catalog(),
                           owner=cfg.OWNER_NAME, app_title=cfg.APP_TITLE,
                           public_mode=cfg.IS_PUBLIC)


# ============================================================ api
@app.route("/api/projects")
def api_projects():
    return jsonify(load_catalog())


@app.route("/api/projects/<pid>")
def api_project(pid):
    project = find_project(pid)
    if not project:
        abort(404)
    return jsonify(project)


@app.route("/api/stats")
def api_stats():
    cat = load_catalog()
    langs = {}
    for c in cat["categories"]:
        for p in c["projects"]:
            if p["exists"]:
                for t in p["tech"]:
                    langs[t] = langs.get(t, 0) + 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:12]
    return jsonify({
        "meta": cat["meta"],
        "languages": [{"name": n, "count": n2} for n, n2 in top],
        "categories": [
            {"id": c["id"], "title": c["title"], "color": c["color"],
             "count": len(c["projects"])} for c in cat["categories"]
        ],
        "publicMode": cfg.IS_PUBLIC,
    })


@app.route("/api/read")
def api_read():
    """
    Read one source file from the workspace for the in-app code browser.

    Disabled entirely in public mode - on a shared server this endpoint
    would otherwise hand out the contents of your project folders.
    """
    if cfg.IS_PUBLIC:
        return jsonify({"ok": False,
                        "error": "Code browser is disabled in public mode"}), 403

    raw = (request.args.get("path") or "").strip()
    if not raw:
        abort(400)

    target = resolve_in_workspace(raw)

    if target.is_dir():
        try:
            entries = sorted(target.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            abort(500)
        items = []
        for child in entries[:MAX_LIST_ITEMS]:
            try:
                st = child.stat()
            except OSError:
                continue
            items.append({"name": cfg.scrub(child.name), "dir": child.is_dir(),
                          "kb": round(st.st_size / 1024, 1)})
        return jsonify({"type": "dir", "items": items})

    if target.suffix.lower() not in TEXT_EXT:
        return jsonify({"type": "binary",
                        "message": "Binary file - cannot display"})

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(MAX_READ_BYTES)
        size = target.stat().st_size
    except OSError:
        abort(500)

    return jsonify({"type": "file", "name": cfg.scrub(target.name),
                    "lines": text.count("\n") + 1,
                    "kb": round(size / 1024, 1),
                    "content": cfg.scrub(text)})


@app.route("/api/wallet")
def api_wallet():
    conn = db()
    try:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, name, email, balance FROM accounts ORDER BY id")]
    finally:
        conn.close()
    return jsonify(rows)


@app.route("/api/wallet/send", methods=["POST"])
def api_wallet_send():
    body = request.get_json(silent=True) or {}
    try:
        frm = int(body.get("from", 1))
        to = int(body.get("to", 3))
        amount = round(float(body.get("amount", 0)), 2)
        note = cfg.scrub(str(body.get("note", "Transfer")))[:120]
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    if amount <= 0 or amount > 10_000_000:
        return jsonify({"ok": False, "error": "Invalid amount"}), 400
    if frm == to:
        return jsonify({"ok": False, "error": "Cannot send to yourself"}), 400

    conn = db()
    try:
        src = conn.execute("SELECT id, name, balance FROM accounts WHERE id=?",
                           (frm,)).fetchone()
        dst = conn.execute("SELECT id, name FROM accounts WHERE id=?", (to,)).fetchone()
        if not src or not dst:
            return jsonify({"ok": False, "error": "Account not found"}), 404
        if src["balance"] < amount:
            return jsonify({"ok": False, "error": "Insufficient balance"}), 400

        conn.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, frm))
        conn.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (amount, to))
        conn.execute("INSERT INTO transfers (frm,to_id,amount,note,ts) VALUES (?,?,?,?,?)",
                     (frm, to, amount, note,
                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        log.info("wallet: transfer of %.2f completed", amount)
        return jsonify({"ok": True, "message": f"Sent to {dst['name']}"})
    except sqlite3.Error:
        conn.rollback()
        log.exception("wallet transaction failed")
        return jsonify({"ok": False, "error": "Transaction failed"}), 500
    finally:
        conn.close()


@app.route("/api/wallet/history")
def api_wallet_history():
    conn = db()
    try:
        rows = [dict(r) for r in conn.execute(
            """
            SELECT t.id, t.amount, t.note, t.ts,
                   a.name AS frm_name, b.name AS to_name
            FROM transfers t
            JOIN accounts a ON a.id = t.frm
            JOIN accounts b ON b.id = t.to_id
            ORDER BY t.id DESC LIMIT 40
            """)]
    finally:
        conn.close()
    return jsonify(rows)


@app.route("/api/wallet/reset", methods=["POST"])
def api_wallet_reset():
    conn = db()
    try:
        conn.execute("DELETE FROM transfers")
        conn.execute("UPDATE accounts SET balance=0")
        for i, (_n, _e, bal) in enumerate(DEMO_ACCOUNTS, start=1):
            conn.execute("UPDATE accounts SET balance=? WHERE id=?", (bal, i))
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        return jsonify({"ok": False}), 500
    finally:
        conn.close()
    return jsonify({"ok": True})


@app.route("/api/rescan", methods=["POST"])
def api_rescan():
    """Rebuild the catalogue by re-running build_catalog.py."""
    if cfg.IS_PUBLIC:
        return jsonify({"ok": False, "error": "Rescan is disabled in public mode"}), 403
    try:
        r = subprocess.run([sys.executable, str(BUILDER)],
                           capture_output=True, text=True, timeout=120,
                           cwd=str(HERE))
        log.info("rescan rc=%s", r.returncode)
        return jsonify({"ok": r.returncode == 0})
    except (OSError, subprocess.SubprocessError):
        log.exception("rescan failed")
        return jsonify({"ok": False, "error": "Rescan failed"}), 500


# ============================================================ errors
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
def err_client(e):
    code = getattr(e, "code", 404)
    if want_json():
        return jsonify({"ok": False, "error": "Request rejected"}), code
    return render_template("404.html", code=code,
                           msg="That request was blocked or does not exist."), code


@app.errorhandler(500)
@app.errorhandler(Exception)
def err_server(e):
    # never leak a traceback, a path or an internal message to the browser
    log.exception("unhandled error")
    if want_json():
        return jsonify({"ok": False, "error": "Internal server error"}), 500
    return render_template("500.html"), 500


# ============================================================ boot
def main():
    init_db()
    cat = load_catalog()
    meta = cat.get("meta", {})

    print("=" * 60)
    print(f"  {cfg.APP_TITLE}")
    print(f"  {meta.get('projects', 0)} projects  |  "
          f"{meta.get('files', 0)} files")
    print(f"  mode: {cfg.MODE}   secret key: {SECRET_SOURCE}")
    print("-" * 60)
    print(f"  open  ->  http://{cfg.HOST}:{cfg.PORT}")
    print(f"  stop  ->  Ctrl + C")
    print("=" * 60)

    if cfg.HOST not in ("127.0.0.1", "localhost", "::1"):
        log.warning("Binding to %s - this app has no login. "
                    "Only do that on a trusted network.", cfg.HOST)

    app.run(host=cfg.HOST, port=cfg.PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()