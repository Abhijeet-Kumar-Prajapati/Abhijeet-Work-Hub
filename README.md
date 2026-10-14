# ⚡ Work Hub

**Ek software. Saara kaam. Ek jagah.**

Ek complete application jo har project ko ek hi dashboard me dikhati hai —
Flask apps, AI assistants, web projects, Android apps aur practice files —
sab kuch automatically scan hoke.

---

## 🔒 Security & Privacy

Ye project **public GitHub repository ke liye taiyar** hai.

### Kya nahi hai isme

| Check | Status |
|---|---|
| Windows user name (`C:\Users\<you>`) | ✅ kabhi nahi likha jaata |
| Absolute file paths | ✅ sirf **relative** path |
| Email addresses | ✅ scrub ho jaate hain |
| API keys / tokens / passwords | ✅ koi hard-coded nahi |
| `.env` aur secret key | ✅ `.gitignore` me hain |
| SQLite database (`hub.db`) | ✅ git-ignore, runtime pe banta hai |
| `__pycache__`, `venv`, logs | ✅ git-ignore |

### Kya protect karta hai app ko

- **Session key** — pehli run pe 32-byte random key banti hai aur
  `data/.secret_key` me cache hoti hai (git-ignored). Koi default weak key nahi.
- **Jailed file reader** — `..` traversal, drive letters, UNC paths, null
  bytes aur symlinks reject hote hain; real path resolve karke workspace ke
  andar hi rehne diya jaata hai.
- **Security headers** — har response pe CSP, `nosniff`, `X-Frame-Options:
  DENY`, `no-referrer`, `Permissions-Policy`.
- **Rate limiting** — saare POST/PUT/DELETE endpoints per-client limited hain.
- **No info leak** — error page pe traceback, path ya internal message nahi jata.
- **Parameterized SQL** — koi string query concatenation nahi.
- **No `eval()`** — calculator ka apna hand-written expression parser hai.
- **Localhost only** — default `127.0.0.1` par bind hota hai.

### `HUB_MODE=public`

Agar koi ise kisi server pe chalana chahe jahan doosre log aa sakte hain:

```bash
HUB_MODE=public python app.py
```

Isse **code browser** aur **rescan** dono band ho jaate hain (403),
taaki koi aapke project files na padh sake.

---

## 🚀 Chalane ke tarike

### 1. One click

`run.bat` par **double click** karo. Browser khud khulta hai.

### 2. Terminal se

```bash
pip install flask
python app.py
```

Browser me kholo → **http://127.0.0.1:5000**

### 3. Bina Flask ke (offline)

`templates/index.html` ko directly browser me kholo.
Baaqi sab chalega — wallet demo browser me hi chalega.

---

## ⚙️ Configuration

`.env.example` ko `.env` me copy karo aur edit karo.
`.env` git-ignore hota hai, isliye private rehta hai.

| Setting | Default | Kaam |
|---|---|---|
| `OWNER_NAME` | `Abhijeet` | sidebar me naam |
| `APP_TITLE` | `Abhijeet Work Hub` | browser tab ka title |
| `WORKSPACE_ROOT` | `./workspace` | wo folder jisme projects hain |
| `SECRET_KEY` | *(auto)* | apni key doge to use hogi |
| `HUB_MODE` | `local` | `public` = code browser off |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | network binding |

Apne projects scan karne ke liye:

```bash
WORKSPACE_ROOT=/path/to/your/projects python build_catalog.py
```

---

## 📦 Kya kya hai isme

| Section | Kya milega |
|---|---|
| **Dashboard** | Projects, files, size, languages + featured work |
| **Projects** | Search, filter aur detail popup |
| **Live Demos** | Calculator, Media Player, To-Do, **PayPal Wallet** |
| **Code Browser** | Workspace ke asli source files, syntax highlighting |
| **Skills** | Language-wise usage bars + project timeline |
| **About** | Architecture, privacy notes, rescan |

### 5 Categories

1. **Full Stack Apps** — PayPal Clone, Charvis AI, Voice Assistant, Launcher
2. **Web Projects** — Media Player, Calculator, Blogging Platform, Portfolio…
3. **Android Apps** — Alarm Clock, Attendance (Firebase), To-Do, Quote of Day
4. **AI Projects** — Computer Vision, AI Lab, Research Pages
5. **Practice** — 150+ Python files, C / C++ / Java / JavaScript

---

## 🗂 Structure

```
├── app.py              ← Flask backend (API + file reader + wallet DB)
├── hub_config.py       ← config, secret key, path safety, scrubbing
├── build_catalog.py    ← workspace scan → data/projects.json
├── run.bat             ← one click launcher
├── requirements.txt
├── .env.example        ← copy to .env (git-ignored)
├── .gitignore
│
├── data/
│   └── projects.json   ← auto-generated, sanitised catalogue
│
├── templates/          ← index.html, 404.html, 500.html
├── static/
│   ├── css/style.css   ← design system
│   └── js/app.js       ← frontend + live demos
└── workspace/          ← placeholder folder for your projects
```

---

## ⚙️ Kaise kaam karta hai

```
WORKSPACE_ROOT ──► build_catalog.py ──► data/projects.json
                                             │
                                             ▼
                                   app.py (Flask API)
                                             │
                                             ▼
                              templates/index.html + static
```

---

## 🔄 Naya kaam add karna ho?

```bash
python build_catalog.py
```

Ya app me **About → Rescan workspace**. Kuch manual karne ki zaroorat nahi.

---

## 🛠 Tech stack

**Backend:** Python, Flask, SQLite
**Frontend:** HTML5, CSS3 (custom properties, glassmorphism), Vanilla JS
**Data:** JSON catalogue + SQLite

