#!/usr/bin/env python3
"""
Build a completely static copy of the hub.

The Flask app needs a server running behind it. GitHub Pages has no
server, but the frontend already falls back to the catalogue embedded
in the page, so the entire dashboard can be exported as plain HTML and
published anywhere that serves files.

    python build_static.py

Writes into the repository root:

    index.html   the exported site   (commit this to publish)
    404.html     the not-found page
    .nojekyll    stops Pages from running Jekyll over the export

Nothing else is copied on purpose: static/ and data/ already sit at the
repository root and are referenced by a relative path, so they are
served exactly as they are.

This script never imports hub_config, because importing it would
generate data/.secret_key as a side effect. Settings are read straight
from .env instead, and .env stays git-ignored.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TPL_DIR = HERE / "templates"
DATA_FILE = HERE / "data" / "projects.json"


# ============================================================ settings
def read_env(name, default=""):
    """Read one key out of .env without pulling in hub_config."""
    env = HERE / ".env"
    if not env.exists():
        return default
    try:
        text = env.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return default
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == name:
            value = value.strip().strip('"').strip("'")
            return value or default
    return default


# ============================================================ jinja glue
def make_url_for(base):
    """Stand-in for Flask's url_for.

    Flask would emit /static/css/style.css. An absolute path is wrong
    for a project site published under /<repo>/, so the export uses a
    relative one instead, which works from any folder depth.
    """
    def url_for(endpoint, **kw):
        if endpoint == "static":
            return base + "static/" + kw.get("filename", "")
        return base or "./"
    return url_for


def build_env(base):
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        sys.exit("Jinja2 is not installed.  pip install jinja2")
    env = Environment(
        loader=FileSystemLoader(str(TPL_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.globals["url_for"] = make_url_for(base)
    return env


# ============================================================ export
def export(env, out_dir, ctx):
    """Render each template into out_dir.

    ctx carries the shared variables (owner, app_title, catalog). The
    error pages ignore them, which is fine.
    """
    targets = [
        ("index.html", "index.html", {"public_mode": True}),
        ("404.html",   "404.html",   {"code": 404}),
    ]

    written = []
    for src, dst, extra in targets:
        src_path = TPL_DIR / src
        if not src_path.exists():
            print(f"  skip  {src} (template missing)")
            continue
        html = env.get_template(src).render(**{**ctx, **extra})
        out_path = out_dir / dst
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # utf-8 without a BOM: a BOM makes browsers ignore the charset
        # declaration and GitHub Pages serves the file as-is
        out_path.write_text(html, encoding="utf-8", newline="\n")
        written.append((dst, len(html)))

    # Pages runs Jekyll over a branch deploy unless this file is present
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    written.append((".nojekyll", 0))
    return written


def main():
    ap = argparse.ArgumentParser(description="Export the hub as a static site.")
    ap.add_argument("--base", default="./",
                    help="prefix for asset paths (default: ./ ). Use '' for "
                         "a site served from the domain root.")
    args = ap.parse_args()

    if not DATA_FILE.exists():
        sys.exit("data/projects.json is missing - run:  python build_catalog.py")

    catalog = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    meta = catalog.get("meta", {}) or {}
    owner = read_env("OWNER_NAME", meta.get("owner") or "Developer")
    title = read_env("APP_TITLE", meta.get("app") or "Work Hub")

    n_projects = sum(len(c.get("projects") or []) for c in catalog.get("categories") or [])
    n_files = meta.get("files") or 0

    print()
    print("  Abhijeet Work Hub - static export")
    print("  " + "-" * 42)
    print(f"  catalogue : {n_projects} projects, {n_files:,} files")
    print(f"  title     : {title}")
    print(f"  base path : {args.base or '(site root)'}")
    print()

    env = build_env(args.base)
    for name, size in export(env, HERE, {"catalog": catalog,
                                         "owner": owner,
                                         "app_title": title}):
        print(f"  wrote  {name:<14} {size:>8,} bytes")

    print()
    print("  Done. static/ and data/ are served as-is from the repo root.")
    print("  Commit index.html to publish, or upload the folder anywhere.")
    print()


if __name__ == "__main__":
    main()
