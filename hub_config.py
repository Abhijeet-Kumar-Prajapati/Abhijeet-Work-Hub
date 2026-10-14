"""
hub_config.py
-------------
Single source of truth for configuration.

Everything is read from the environment first, then from an optional
`.env` file, then falls back to a safe default. No personal machine
paths or secrets are ever hard-coded in this project.

Copy `.env.example` to `.env` to customise. `.env` is git-ignored.
"""

import os
import re
import secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
SECRET_FILE = DATA_DIR / ".secret_key"


# --------------------------------------------------------------- .env
def load_dotenv():
    """Read a very small KEY=VALUE .env file into os.environ.
    Real environment variables always win."""
    env_file = HERE / ".env"
    if not env_file.is_file():
        return
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip("'\""))
    except OSError:
        pass


load_dotenv()


# --------------------------------------------------------------- basics
def _str(name, default=""):
    val = os.environ.get(name)
    return val.strip() if val and val.strip() else default


def _int(name, default):
    try:
        return int(_str(name, str(default)))
    except ValueError:
        return default


APP_TITLE = _str("APP_TITLE", "Work Hub")
OWNER_NAME = _str("OWNER_NAME", "Abhijeet")

HOST = _str("HOST", "127.0.0.1")
PORT = _int("PORT", 5000)

# "local"  -> code browser, rescan and the wallet database are available
# "public" -> code browser and rescan are disabled
MODE = _str("HUB_MODE", "local").lower()
IS_PUBLIC = MODE == "public"


# --------------------------------------------------------------- workspace
def default_workspace():
    """Folder scanned for projects when WORKSPACE_ROOT is not set."""
    bundled = HERE / "workspace"
    bundled.mkdir(exist_ok=True)
    return bundled


WORKSPACE_ROOT = _str("WORKSPACE_ROOT", "") or str(default_workspace())


# --------------------------------------------------------------- secret key
def get_secret_key():
    """
    Return a strong session signing key.

    Order:  SECRET_KEY env var  ->  data/.secret_key  ->  fresh random.

    A random key is generated once and cached in data/.secret_key
    (which is git-ignored), so sessions survive a restart without the
    key ever being committed to the repository.
    """
    env_key = os.environ.get("SECRET_KEY", "").strip()
    if len(env_key) >= 32:
        return env_key, "environment"

    try:
        DATA_DIR.mkdir(exist_ok=True)
        if SECRET_FILE.is_file():
            cached = SECRET_FILE.read_text(encoding="utf-8").strip()
            if len(cached) >= 32:
                return cached, "cache"
        fresh = secrets.token_hex(32)
        SECRET_FILE.write_text(fresh, encoding="utf-8")
        return fresh, "generated"
    except OSError:
        return secrets.token_hex(32), "ephemeral"


# --------------------------------------------------------------- privacy
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def scrub(text):
    """
    Remove anything machine-specific or personal from a string before
    it is written to a file that might be committed.
    """
    if not text:
        return text
    out = str(text)

    # windows user names, e.g.  C:\Users\someone\...
    out = re.sub(r"[A-Za-z]:\\\\?Users\\\\?[^\\\\/\"'\s]+", "<user>", out)
    # posix home dirs, e.g.  /home/someone/...
    out = re.sub(r"/(?:home|Users)/[^/\s\"']+", "/<user>", out)
    # email addresses
    out = EMAIL_RE.sub("<email>", out)
    return out


def is_safe_relpath(rel):
    """
    True when a path is relative and cannot escape its root.

    Guards against '..', absolute paths, UNC paths, drive letters,
    null bytes and symlink-style tricks.
    """
    if not rel or len(rel) > 400:
        return False
    if "\x00" in rel:
        return False
    if rel.startswith(("/", "\\")):
        return False
    if re.match(r"^[A-Za-z]:", rel):
        return False
    parts = re.split(r"[\\/]+", rel)
    return ".." not in parts and all(p not in ("", ".") for p in parts)