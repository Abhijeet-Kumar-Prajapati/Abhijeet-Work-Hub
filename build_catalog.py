"""
build_catalog.py
----------------
Scans WORKSPACE_ROOT and writes `data/projects.json`.

PRIVACY BY DEFAULT
------------------
The generated file is safe to commit to a public repository:

  * absolute paths are NEVER written
  * Windows / POSIX user names are never written
  * email addresses are never written
  * only paths RELATIVE to WORKSPACE_ROOT appear

Run:
    python build_catalog.py

Point it at your own work with:
    WORKSPACE_ROOT=D:\\My Projects   python build_catalog.py
or by copying `.env.example` to `.env` and editing it.
"""

import json
import os
import sys
import datetime
from pathlib import Path

# some portable / embedded Python builds do not put the script folder on
# sys.path, so add it explicitly to make the local import work everywhere
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hub_config as cfg

BASE = Path(cfg.WORKSPACE_ROOT).resolve()
OUT = cfg.DATA_DIR / "projects.json"

SKIP_DIRS = {".venv", "venv", "__pycache__", ".pytest_cache", "node_modules",
             ".git", ".cursor", ".vscode", ".idea", "env"}
SKIP_EXT = {".log", ".pdf", ".db", ".pyc", ".exe", ".zip", ".7z", ".rar"}


# --------------------------------------------------------------------- scan
def scan(target):
    """Return (exists, file_count, total_kb, latest_mtime) for a file or folder."""
    p = BASE / target if target else BASE
    if not p.exists():
        return (False, 0, 0, None)

    files, total, latest = 0, 0, None

    if p.is_file():
        try:
            return (True, 1, p.stat().st_size // 1024,
                    datetime.datetime.fromtimestamp(p.stat().st_mtime))
        except OSError:
            return (True, 0, 0, None)

    for root, dirs, names in os.walk(p):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            fp = Path(root) / n
            if fp.suffix.lower() in SKIP_EXT:
                continue
            try:
                total += fp.stat().st_size // 1024
                files += 1
                mt = datetime.datetime.fromtimestamp(fp.stat().st_mtime)
                if latest is None or mt > latest:
                    latest = mt
            except OSError:
                pass
    return (True, files, total, latest)


# ---------------------------------------------------------------- catalogue
# `subpath` values are RELATIVE to WORKSPACE_ROOT and are the only paths
# that ever leave this script.
CATALOG = [
    ("fullstack", "Full Stack Apps", "#6366f1", [
        dict(
            id="paypal-clone", title="PayPal Clone", highlight=True, demo="wallet",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet",
            desc="A working money-transfer web app. Register, log in, send money to any "
                 "user and watch the transaction history update in real time.",
            tech=["Python", "Flask", "SQLite", "SQLAlchemy", "Flask-Login", "WTForms", "Jinja2"],
            features=[
                "Email registration and login via Flask-Login",
                "Werkzeug password hashing",
                "Send money with balance validation",
                "Per-user transaction history",
                "CSRF protection through Flask-WTF",
                "Custom 404 and 500 error pages",
            ],
            entry="app.py",
        ),
        dict(
            id="charvis-ai", title="Charvis AI Assistant", highlight=True,
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet",
            desc="A Jarvis-style desktop voice assistant with an Iron Man themed GUI. "
                 "Listens to commands, speaks back, controls the PC and plays media.",
            tech=["Python", "customtkinter", "SpeechRecognition", "pyttsx3", "pycaw",
                  "PyTube", "pyjokes", "wikipedia", "wolframalpha", "win10toast"],
            features=[
                "Offline and online voice command recognition",
                "Text to speech with male and female voices",
                "System volume control through pycaw",
                "YouTube search, streaming and download",
                "Wikipedia and WolframAlpha answers",
                "Windows toast notifications",
                "Auto-restart if the process crashes",
            ],
            entry="charvis_ai.py",
        ),
        dict(
            id="voice-assistant", title="Voice Assistant Core",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet",
            desc="The recognition and speech engine behind the assistant, tuned with "
                 "adaptive energy thresholds so it reacts faster in noisy rooms.",
            tech=["Python", "pyttsx3", "SpeechRecognition", "logging"],
            features=[
                "Adaptive energy threshold",
                "Tuned pause and phrase thresholds",
                "Microphone auto-detection",
                "Project manager integration",
            ],
            entry="voice_assistant.py",
        ),
        dict(
            id="charvis-launcher", title="Charvis Auto-Launcher",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet",
            desc="A Windows startup launcher that boots the assistant with the correct "
                 "virtual environment and restarts it automatically after a crash.",
            tech=["Python", "subprocess", "tkinter", "logging"],
            features=[
                "Auto-detect the venv interpreter",
                "Crash detection and restart loop",
                "Startup log file",
                "Desktop shortcut creator",
            ],
            entry="start_charvis.pyw",
        ),
    ]),

    ("web", "Web Projects", "#0ea5e9", [
        dict(
            id="media-player", title="Universal Media Player", highlight=True, demo="player",
            subpath="player.html",
            desc="A single-file media player that handles audio and video with a clean "
                 "16:9 stage, playlist and playback controls.",
            tech=["HTML", "CSS", "JavaScript"],
            features=["Audio and video playback", "16:9 responsive stage",
                      "Custom control bar", "Playlist support"],
            entry="player.html",
        ),
        dict(
            id="calculator", title="Calculator", demo="calculator",
            subpath=r"try code\projact wab develpor\CALCULATOR",
            desc="A grid based calculator with a live display, built with clean "
                 "HTML, CSS and vanilla JavaScript.",
            tech=["HTML", "CSS", "JavaScript"],
            features=["4 column button grid", "Live expression display", "Error handling"],
            entry="HTML Structure.html",
        ),
        dict(
            id="blogging-platform", title="Blogging Platform",
            subpath=r"try code\projact wab develpor\BLOGGING PLATFORM",
            desc="The front end of a blogging platform that pulls live posts from the "
                 "GitHub API using fetch().",
            tech=["HTML", "JavaScript", "GitHub API", "fetch()"],
            features=["Live GitHub API fetch", "Backend and frontend split",
                      "Async rendering"],
            entry="frontdevepoler.html",
        ),
        dict(
            id="portfolio", title="Portfolio Page",
            subpath=r"try code\projact wab develpor\PORTFOLIO",
            desc="A personal portfolio layout built to showcase projects and skills.",
            tech=["HTML", "CSS"],
            features=["Responsive layout", "Project grid", "Skills section"],
            entry="HTML Structure.html",
        ),
        dict(
            id="tribute-page", title="Tribute Page",
            subpath=r"try code\projact wab develpor\TRIBUTE PAGE",
            desc="A tribute page layout dedicated to a person, with a hero section "
                 "and a biography block.",
            tech=["HTML", "CSS"],
            features=["Hero section", "Biography layout", "Responsive"],
            entry="index.html",
        ),
        dict(
            id="landing-page", title="Landing Pages",
            subpath=r"try code\projact wab develpor\LANDING PAGE",
            desc="A marketing landing page with a hero section, call to action and "
                 "feature blocks.",
            tech=["HTML", "CSS"],
            features=["Hero and CTA", "Feature grid", "Responsive"],
            entry="index.html",
        ),
        dict(
            id="login-pages", title="Login and Logo Pages",
            subpath=r"try code\HTML\html logo code",
            desc="A batch of login screens, logo layouts and web form studies built "
                 "while learning HTML structure.",
            tech=["HTML", "CSS"],
            features=["Multiple layouts", "Form studies", "Logo experiments"],
            entry="LOG.HTML",
        ),
    ]),

    ("android", "Android Apps", "#22c55e", [
        dict(
            id="alarm-clock", title="Alarm Clock App", highlight=True,
            subpath=r"try code\ANDROID APP DEVELOPMENT\ALARM CLOCK APP",
            desc="A native Android alarm clock written in Kotlin, with a home screen "
                 "and a dedicated alarm setting screen.",
            tech=["Kotlin", "Android"],
            features=["Home screen activity", "Alarm setting activity",
                      "Multi-activity navigation"],
            entry="Home Screen Activity.kt",
        ),
        dict(
            id="university-attendance", title="University Attendance",
            subpath=r"try code\ANDROID APP DEVELOPMENT\UNIVERSITY ATTENDANCE APP",
            desc="An attendance tracker that stores student records in Firebase "
                 "Firestore in real time.",
            tech=["JavaScript", "Firebase", "Firestore"],
            features=["Firebase config", "Real-time database", "Attendance records"],
            entry="App .js",
        ),
        dict(
            id="todo-list", title="To-Do List App",
            subpath=r"try code\ANDROID APP DEVELOPMENT\TO-DO LIST APP",
            desc="A task manager with add, complete and delete, styled with its own "
                 "CSS theme.",
            tech=["HTML", "CSS", "JavaScript"],
            features=["Add, complete and delete tasks", "Persistent list", "Custom CSS"],
            entry="Structure.html",
        ),
        dict(
            id="quote-of-day", title="Quote of the Day",
            subpath=r"try code\ANDROID APP DEVELOPMENT\QUOTE OF THE DAY APP",
            desc="A motivational quote app that fetches a fresh quote on every open.",
            tech=["JavaScript", "API"],
            features=["Random quote fetch", "Share a quote", "Refresh on launch"],
            entry="react.js",
        ),
        dict(
            id="window-notification", title="Desktop Notification",
            subpath=r"try code\ANDROID APP DEVELOPMENT\WINDOW NOTIFICATION USING JAVA CODE",
            desc="A small Python utility that fires native Windows notifications "
                 "from the desktop.",
            tech=["Python", "Tkinter"],
            features=["Native toast popup", "Runs standalone"],
            entry="Design a Notification Window.py",
        ),
    ]),

    ("ai", "AI Projects", "#a855f7", [
        dict(
            id="computer-vision", title="Computer Vision Study",
            subpath=r"try code\Artificial Intelligence\computer.py",
            desc="An early look at computer vision and image based learning in Python.",
            tech=["Python", "AI"],
            features=["Image processing basics", "Python scripting"],
            entry="computer.py",
        ),
        dict(
            id="ai-lab", title="AI Lab Experiments",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet\PYTHON\---projaect 2",
            desc="A folder of AI experiments covering search, parsing and dataset "
                 "handling.",
            tech=["Python", "AI", "Data"],
            features=["Dataset handling", "Parsing experiments",
                      "Pattern and number problems", "Text processing"],
            entry="Artificial Intelligence..py",
        ),
        dict(
            id="research-pages", title="Interactive Research Pages",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet\HTML",
            desc="A set of self-contained research pages: AI search, graph analysis, "
                 "human studies and study material.",
            tech=["HTML", "CSS", "JavaScript"],
            features=["AI search engine", "Graph visualisation",
                      "Study material viewer", "Standalone test suite"],
            entry="ai-search.html",
        ),
    ]),

    ("practice", "Practice and Learning", "#f59e0b", [
        dict(
            id="python-practice", title="Python Practice (150+ files)", highlight=True,
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet\PYTHON",
            desc="Fourteen practice sets covering Python from print() through to "
                 "inheritance, decorators, recursion and file handling.",
            tech=["Python"],
            features=["Lists, dicts, sets and tuples",
                      "OOP, inheritance and operator overloading",
                      "File handling with and try-finally",
                      "Recursion and lambdas",
                      "Matrix maths and number theory"],
            entry=r"learn code 14\map-filter-reduce.py",
        ),
        dict(
            id="language-basics", title="Language Basics",
            subpath=r"try code\abhijeet fro\abhijeet fro\abhijeet",
            desc="Starter practice in C, C++, Java, JavaScript and CSS.",
            tech=["C", "C++", "Java", "JavaScript", "CSS"],
            features=["C and C++ basics", "Java programs",
                      "Node and Express server", "CSS styling"],
            entry="CSS",
        ),
    ]),
]


# -------------------------------------------------------------------- build
def build():
    categories, total_files, total_kb = [], 0, 0

    for cid, ctitle, ccolor, projects in CATALOG:
        items = []
        for p in projects:
            exists, fcount, kb, latest = scan(p["subpath"])
            items.append({
                "id": p["id"],
                "title": p["title"],
                "desc": p["desc"],
                "tech": p["tech"],
                "features": p.get("features", []),
                "exists": exists,
                "files": fcount,
                "kb": kb,
                "date": latest.strftime("%Y-%m-%d") if latest else None,
                "demo": p.get("demo"),
                "entry": p.get("entry"),
                "highlight": bool(p.get("highlight", False)),
                # relative only - never an absolute path
                "subpath": p["subpath"].replace("\\", "/"),
            })
            if exists:
                total_files += fcount
                total_kb += kb

        categories.append({"id": cid, "title": ctitle,
                           "color": ccolor, "projects": items})

    catalog = {
        "meta": {
            "app": cfg.APP_TITLE,
            "owner": cfg.OWNER_NAME,
            "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "categories": len(categories),
            "projects": sum(len(c["projects"]) for c in categories),
            "files": total_files,
            "kb": total_kb,
            # no absolute base path is published
            "workspace_set": True,
        },
        "categories": categories,
    }

    cfg.DATA_DIR.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    missing = [p["title"] for c in categories for p in c["projects"] if not p["exists"]]
    print(f"[OK] {OUT.name}  ->  {catalog['meta']['projects']} projects, "
          f"{total_files} files, {total_kb / 1024:.1f} MB")
    if not BASE.exists():
        print(f"[!] Workspace folder not found: {BASE}")
        print("    Set WORKSPACE_ROOT in .env to point at your projects.")
    if missing:
        print(f"[i] not found on disk (listed with 0 files): {len(missing)}")
    return catalog


if __name__ == "__main__":
    build()