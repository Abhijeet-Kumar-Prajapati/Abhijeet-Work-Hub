# ⚡ Work Hub

**Ek software. Saara kaam. Ek jagah.**

Ek complete application jo har project ko ek hi dashboard me dikhati hai —
Flask apps, AI assistants, web projects, Android apps aur practice files —
sab kuch automatically scan hoke.

🌐 **Live chal raha hai:** <https://abhijeet-kumar-prajapati.github.io/Abhijeet-Work-Hub/>

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

### 4. Online — GitHub Pages (free, static)

```bash
pip install jinja2
python build_static.py
```

Ye `index.html`, `404.html` aur `.nojekyll` ko repo root me likhta hai —
catalogue page ke andar hi embed ho jaata hai. Bas push kar do:

```bash
git add index.html 404.html .nojekyll
git commit -m "static export"
git push
```

GitHub Pages khud publish kar dega. **Flask ki zaroorat nahi** — frontend API
fail hone par embedded catalogue par switch ho jaata hai, aur code browser
aur rescan apne aap chhup jaate hain.

Jab bhi catalogue badle, `python build_static.py` dobara chala ke commit karo.

### 5. Online — poora backend (Render, free)

Sirf static nahi, **live Flask backend + SQLite wallet** chahiye to:

1. [render.com](https://render.com) → **New → Blueprint**
2. `Abhijeet-Work-Hub` repo select karo → **Apply**

`render.yaml` me sab already set hai — `HUB_MODE=public`, `HOST=0.0.0.0`,
gunicorn. Link kuch hi der me mil jayega, jaise `abhijeet-work-hub.onrender.com`.

> Free plan 15 min idle ke baad sleep ho jata hai; wapas aane me 30–50s lagte hain.

Railway / Heroku par bhi same chalta hai — `Procfile` ready hai.

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
| **Projects** | Search (highlight + clear), category chips, **6 sort orders**, **Surprise me**, detail popup |
| **Live Demos** | Calculator, Media Player, To-Do, **PayPal Wallet** |
| **Code Browser** | Workspace ke asli source files, syntax highlighting |
| **Skills** | Language-wise usage bars + project timeline — **ek click me filter** |
| **About** | Architecture, privacy notes, rescan |

### Extra features

| Feature | Kya karta hai |
|---|---|
| 🌗 **Dark / Light theme** | Sidebar button ya `t` key — choice save rehti hai |
| 🎲 **Surprise me** | Ek random project kholta hai, ya `r` key |
| 🔗 **Shareable links** | `#/p/paypal-clone` jaisa URL — copy karke bhejo, seedha khulega |
| ⌨️ **Keyboard shortcuts** | `?` dabao poora list dikhega |
| ⬆️ **Back to top** | Neeche scroll karne par button |
| 🏷️ **Skill filter** | Skills view me koi bhi technology pe click → sirf uske projects |

### ⌨️ Keyboard shortcuts

| Key | Kaam |
|---|---|
| `/` | Search box pe seedha chala jao |
| `t` | Dark ↔ Light theme badlo |
| `r` | Random project kholo |
| `?` | Shortcut ki list |
| `Esc` | Dialog band karo |

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
├── build_static.py     ← GitHub Pages ke liye static export
├── run.bat             ← one click launcher
├── requirements.txt
├── render.yaml         ← one-click deploy on Render
├── Procfile            ← Railway / Heroku ke liye
├── .env.example        ← copy to .env (git-ignored)
├── .gitignore
│
├── index.html          ← build_static.py ka output (Pages yahi serve karta hai)
├── 404.html            ← ← wahi, custom not-found page
│
├── data/
│   └── projects.json   ← auto-generated, sanitised catalogue
│
├── templates/          ← Jinja source: index.html, 404.html, 500.html
├── static/
│   ├── css/style.css   ← design system (dark + light theme)
│   └── js/app.js       ← frontend + live demos + keyboard routing
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
python build_catalog.py     # workspace dubara scan karo
python build_static.py      # online copy refresh karo
git add -A && git commit -m "new project" && git push
```

Ya app me **About → Rescan workspace**. Kuch manual karne ki zaroorat nahi.

> Online copy sirf tab update hogi jab `index.html` rebuild karke push kiya jaye —
> GitHub Pages har push par apne aap publish kar leta hai.

---

## 🛠 Tech stack

**Backend:** Python, Flask, SQLite, Gunicorn
**Frontend:** HTML5, CSS3 (custom properties, glassmorphism, dual theme), Vanilla JS
**Static export:** Jinja2 → plain HTML (GitHub Pages)
**Data:** JSON catalogue + SQLite

