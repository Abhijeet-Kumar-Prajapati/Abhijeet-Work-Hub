/* ============================================================
   Abhijeet Work Hub  -  frontend logic
   Works two ways:
     1. served by Flask  -> full live API
     2. opened as a file -> bundled catalogue + offline demos
   ============================================================ */
(function () {
  "use strict";

  // ---------------------------------------------------- helpers
  const $  = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const ON_FLASK = location.protocol !== "file:";
  // set to true when the server runs with HUB_MODE=public, where the
  // code browser and rescan endpoints are disabled
  let PUBLIC_MODE = document.documentElement.dataset.hubMode === "public";
  const api = async (path, opts) => {
    const r = await fetch(path, opts);
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  };
  const post = (path, body) =>
    api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    });

  const kbTxt = (kb) =>
    kb >= 1024 ? (kb / 1024).toFixed(1) + " MB" : (kb || 0) + " KB";

  const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN");

  const ICONS = {
    fullstack: "⚙", web: "🌐", android: "📱", ai: "❈", practice: "✎"
  };

  // ---------------------------------------------------- catalogue
  let CAT = { meta: {}, categories: [] };
  let ALL = [];          // flat list of projects
  let activeFilter = "all";
  let activeTech = "";   // set when a skill chip is clicked
  let VIEW = "dashboard";// last view shown, so Back returns here

  function readEmbedded() {
    const el = document.getElementById("catalog-data");
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  async function loadCatalog() {
    let data = null;
    if (ON_FLASK) {
      try { data = await api("/api/projects"); } catch (e) { data = null; }
    }
    if (!data || !data.categories || !data.categories.length) data = readEmbedded();
    if (!data || !data.categories) {
      document.body.insertAdjacentHTML("afterbegin",
        '<div style="padding:30px;color:#fca5a5">Could not load the catalogue. Run <code>python build_catalog.py</code> first.</div>');
      return;
    }
    CAT = data;
    ALL = [];
    CAT.categories.forEach((c) => c.projects.forEach((p) => {
      p.categoryId = c.id; p.categoryTitle = c.title; p.color = c.color;
      ALL.push(p);
    }));
    buildUI();
  }

  // ---------------------------------------------------- address bar
  /* Every view and every project gets a real URL, so a link can be copied
     and shared and the browser Back button behaves the way people expect. */
  function setHash(h) {
    const want = "#/" + h;
    if (location.hash !== want) history.pushState(null, "", want);
  }
  function readHash() {
    const m = /^#\/([a-z]+)(?:\/(.+))?$/i.exec(location.hash || "");
    return m ? { kind: m[1].toLowerCase(), arg: m[2] ? decodeURIComponent(m[2]) : "" } : null;
  }

  // ---------------------------------------------------- navigation
  function show(view, push) {
    const target = $("#v-" + view);
    if (!target) return;
    $$(".view").forEach((v) => v.classList.remove("active"));
    target.classList.add("active");
    VIEW = view;
    $$(".nav-item").forEach((n) =>
      n.classList.toggle("active", n.dataset.view === view));
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (push !== false) setHash("v/" + view);
  }

  $$(".nav-item").forEach((n) =>
    (n.onclick = () => show(n.dataset.view)));
  $$("[data-go]").forEach((b) =>
    (b.onclick = () => show(b.dataset.go)));

  // ---------------------------------------------------- build all UI
  function buildUI() {
    const m = CAT.meta || {};
    $("#cProjects").textContent = ALL.length;
    $("#fProjects").textContent = m.projects != null ? m.projects : ALL.length;
    $("#fFiles").textContent = (m.files || 0).toLocaleString();
    $("#fGen").textContent = m.generated ? "scanned " + m.generated : "";

    if (!ON_FLASK) {
      const b = document.createElement("div");
      b.className = "standalone-banner";
      b.innerHTML = "⚠ Running in <b>offline mode</b>. Start the Flask app for live data: " +
        "<code>python app.py</code>";
      $(".main").insertBefore(b, $(".main").firstChild);
      $("#wMode").innerHTML = "⚠ Offline mode - the wallet runs with demo data saved in your browser.";
    }

    /* On a published copy (static build or a public host) there is no Flask
       API behind the page, so anything that needs the server is hidden
       instead of left behind as a button that cannot work. */
    if (PUBLIC_MODE) {
      $$("[data-needs-server]").forEach((el) => (el.style.display = "none"));
      const holder = $("#rescanHolder");
      if (holder) holder.style.display = "none";
    }

    renderStats();
    renderFeatured();
    renderCategories();
    renderFilters();
    renderProjects();
    renderCodePicker();
    renderSkills();
    renderTimeline();
  }

  // ---------------------------------------------------- dashboard
  function renderStats() {
    const m = CAT.meta || {};
    const codes = ALL.reduce((s, p) => {
      const ext = (p.entry || "").split(".").pop();
      return s + 1;
    }, 0);
    const cells = [
      ["Projects", m.projects != null ? m.projects : ALL.length, ""],
      ["Files scanned", (m.files || 0).toLocaleString(), ""],
      ["Total size", kbTxt(m.kb || 0), ""],
      ["Categories", (CAT.categories || []).length, ""],
      ["Languages", new Set(ALL.flatMap((p) => p.tech)).size, ""]
    ];
    $("#dashStats").innerHTML = cells.map(([k, v]) =>
      `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`
    ).join("");
  }

  function cardHTML(p, q) {
    const live = p.demo
      ? `<span class="live">&#9679; LIVE DEMO</span>`
      : (p.exists ? "" : `<span class="missing">folder not found</span>`);
    return `
      <div class="card ${p.highlight ? "hl" : ""}" data-id="${p.id}">
        <div class="card-head">
          <div class="card-ico">${ICONS[p.categoryId] || "◆"}</div>
          <div>
            <h3>${mark(p.title, q)}</h3>
            <div class="cat">${esc(p.categoryTitle)}</div>
          </div>
        </div>
        <p>${mark(p.desc, q)}</p>
        <div class="pills">${p.tech.slice(0, 4).map((t, i) =>
          `<span class="pill ${i % 2 ? "alt" : ""}">${mark(t, q)}</span>`).join("")}</div>
        <div class="card-foot">
          ${live}
          <span>${p.files} files</span>
          <span>${kbTxt(p.kb)}</span>
          ${p.date ? `<span style="margin-left:auto">${p.date}</span>` : ""}
        </div>
      </div>`;
  }

  function renderFeatured() {
    const list = ALL.filter((p) => p.highlight).slice(0, 6);
    $("#featured").innerHTML = list.map(cardHTML).join("");
    wireCards($("#featured"));
  }

  function renderCategories() {
    $("#catCards").innerHTML = CAT.categories.map((c) => `
      <div class="card" data-filter="${c.id}" style="--glow:${c.color}22">
        <div class="card-head">
          <div class="card-ico" style="color:${c.color}">${ICONS[c.id] || "◆"}</div>
          <div>
            <h3>${esc(c.title)}</h3>
            <div class="cat">${c.projects.length} projects</div>
          </div>
        </div>
        <p>${c.projects.slice(0, 3).map((p) => esc(p.title)).join(" · ")}${
          c.projects.length > 3 ? " · …" : ""}</p>
        <div class="card-foot"><span style="color:${c.color}">Open category →</span></div>
      </div>`).join("");

    $$("#catCards .card").forEach((el) => {
      el.onclick = () => {
        show("projects");
        activeFilter = el.dataset.filter;
        renderFilters();
        renderProjects();
      };
    });
  }

  // ---------------------------------------------------- projects view
  function renderFilters() {
    const list = [{ id: "all", title: "All", n: ALL.length }].concat(
      CAT.categories.map((c) => ({ id: c.id, title: c.title, n: c.projects.length, color: c.color }))
    );
    $("#filters").innerHTML = list.map((c) =>
      `<button class="chip ${c.id === activeFilter ? "on" : ""}" data-f="${c.id}">
        ${esc(c.title)} <span style="opacity:.6">${c.n}</span></button>`).join("");
    $$("#filters .chip").forEach((b) =>
      (b.onclick = () => { activeFilter = b.dataset.f; renderProjects(); }));
  }

  /* the "you are filtering by Python" reminder strip */
  function renderActiveFilter() {
    const el = $("#activeFilter");
    if (!activeTech) { el.style.display = "none"; el.innerHTML = ""; return; }
    el.style.display = "block";
    el.innerHTML =
      `<div class="af-in">Showing every project built with <b>${esc(activeTech)}</b>
        <button id="afClear" title="Remove this filter">&#10005;</button></div>`;
    $("#afClear").onclick = () => { activeTech = ""; renderProjects(); };
  }

  const SORTS = {
    new:   (a, b) => (b.date || "").localeCompare(a.date || ""),
    old:   (a, b) => (a.date || "").localeCompare(b.date || ""),
    az:    (a, b) => String(a.title).localeCompare(String(b.title)),
    za:    (a, b) => String(b.title).localeCompare(String(a.title)),
    big:   (a, b) => (b.kb || 0) - (a.kb || 0),
    small: (a, b) => (a.kb || 0) - (b.kb || 0)
  };

  /* wrap each hit of q inside text that has ALREADY been escaped, so the
     highlight can never open an injection hole */
  function mark(text, q) {
    const s = esc(text);
    if (!q) return s;
    const needle = esc(q).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (!needle) return s;
    return s.replace(new RegExp("(" + needle + ")", "gi"), "<mark>$1</mark>");
  }

  function renderProjects() {
    const wrap = $("#searchWrap");
    const raw = $("#search").value || "";
    const q = raw.toLowerCase().trim();
    if (wrap) wrap.classList.toggle("filled", !!raw);

    let list = ALL.filter((p) => activeFilter === "all" || p.categoryId === activeFilter);
    if (activeTech) list = list.filter((p) => p.tech.indexOf(activeTech) !== -1);
    if (q) {
      list = list.filter((p) =>
        (p.title + " " + p.desc + " " + p.tech.join(" ")).toLowerCase().includes(q));
    }
    list = list.slice().sort(SORTS[$("#sortSel").value] || SORTS.new);

    $("#allProjects").innerHTML = list.map((p) => cardHTML(p, q)).join("");
    $("#noResult").style.display = list.length ? "none" : "block";
    $("#resCount").innerHTML = list.length === ALL.length
      ? "<b>" + ALL.length + "</b> projects"
      : "<b>" + list.length + "</b> of " + ALL.length + " projects";
    renderActiveFilter();
    wireCards($("#allProjects"));
  }

  function wireCards(root) {
    $$(".card[data-id]", root).forEach((el) => {
      el.onmousemove = (e) => {
        const r = el.getBoundingClientRect();
        el.style.setProperty("--mx", (e.clientX - r.left) + "px");
      };
      el.onclick = () => openProject(el.dataset.id);
    });
  }

  $("#search").addEventListener("input", renderProjects);

  // ---------------------------------------------------- project modal
  function openProject(id, push) {
    const p = ALL.find((x) => x.id === id);
    if (!p) return;
    if (push !== false) setHash("p/" + id);

    let html = `
      <button class="modal-close" id="mClose">✕</button>
      <h2>${esc(p.title)}</h2>
      <div class="sub">${esc(p.categoryTitle)} · ${p.files} files · ${kbTxt(p.kb)}${
        p.date ? " · " + p.date : ""}</div>
      <p class="desc">${esc(p.desc)}</p>
      <div class="pills">${p.tech.map((t) => `<span class="pill">${esc(t)}</span>`).join("")}</div>`;

    if (p.features && p.features.length) {
      html += `<h4>What it does</h4><ul class="flist">${
        p.features.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>`;
    }
    if (p.subpath) {
      html += `<h4>Location (relative to workspace)</h4><div class="pathbox">${esc(p.subpath)}</div>`;
    }
    html += `<div class="meta-row">
      ${p.demo ? `<button class="btn primary" id="mDemo">▶ Open live demo</button>` : ""}
      ${(PUBLIC_MODE || !p.exists) ? "" : `<button class="btn" id="mCode">&#8984; View code</button>`}
      <button class="btn" id="mShare">&#128279; Copy link</button>
    </div>`;

    const box = $("#modalBox");
    box.innerHTML = html;
    $("#modal").classList.add("open");

    $("#mClose").onclick = closeModal;
    if (p.demo) $("#mDemo").onclick = () => {
      closeModal(); show("demos");
      $$("#demoTabs .tab").forEach((t) => t.classList.toggle("on", t.dataset.demo === p.demo));
      switchDemo(p.demo);
    };
    const codeBtn = $("#mCode");
    if (codeBtn) codeBtn.onclick = () => {
      closeModal(); show("code"); $("#cbProj").value = p.id; openCode(p);
    };
    $("#mShare").onclick = async () => {
      const url = location.origin + location.pathname + "#/p/" + p.id;
      try {
        await navigator.clipboard.writeText(url);
        toast("Link copied - anyone can open this project");
      } catch (e) {
        toast("Copy blocked by the browser - use the address bar");
      }
    };
  }

  function closeModal() {
    if (!$("#modal").classList.contains("open")) return;
    $("#modal").classList.remove("open");
    const h = readHash();
    if (h && h.kind === "p") setHash("v/" + VIEW);
  }
  $("#modal").onclick = (e) => { if (e.target.id === "modal") closeModal(); };

  // ======================================================= DEMOS
  $$("#demoTabs .tab").forEach((t) =>
    (t.onclick = () => {
      $$("#demoTabs .tab").forEach((x) => x.classList.remove("on"));
      t.classList.add("on");
      switchDemo(t.dataset.demo);
    }));

  function switchDemo(name) {
    ["calculator", "player", "todo", "wallet"].forEach((d) =>
      ($("#demo-" + d).style.display = d === name ? "block" : "none"));
    if (name === "wallet") loadWallet();
  }

  // ---------------------------------------------------- calculator
  const KEYS = [
    ["C", "clr"], ["(", "op"], [")", "op"], ["÷", "op"],
    ["7", ""], ["8", ""], ["9", ""], ["×", "op"],
    ["4", ""], ["5", ""], ["6", ""], ["−", "op"],
    ["1", ""], ["2", ""], ["3", ""], ["+", "op"],
    ["0", ""], [".", ""], ["⌫", "clr"], ["=", "eq"]
  ];
  $("#calcGrid").innerHTML = KEYS.map(([k, c]) =>
    `<button class="${c}" data-k="${esc(k)}">${esc(k)}</button>`).join("");

  let cExpr = "";
  const OP = { "÷": "/", "×": "*", "−": "-" };

  function cRender() {
    $("#cVal").textContent = cExpr || "0";
    $("#cExpr").textContent = cExpr;
  }
  /* Hand written expression parser.
     No eval(), no new Function() - the expression is walked token by
     token, so nothing but digits and the four operators can ever run. */
  function evaluate(src) {
    const s = String(src);
    let i = 0;
    const ws = () => { while (i < s.length && s[i] === " ") i++; };

    function factor() {
      ws();
      const c = s[i];
      if (c === "(") { i++; const v = expr(); ws(); if (s[i] === ")") i++; return v; }
      if (c === "-") { i++; return -factor(); }
      if (c === "+") { i++; return factor(); }
      let n = "";
      while (i < s.length && (s[i] >= "0" && s[i] <= "9" || s[i] === ".")) n += s[i++];
      if (n === "") throw new Error("number expected");
      const v = parseFloat(n);
      if (!isFinite(v)) throw new Error("bad number");
      return v;
    }

    function term() {
      let v = factor();
      for (;;) {
        ws();
        if (s[i] === "*") { i++; v *= factor(); }
        else if (s[i] === "/") {
          i++;
          const d = factor();
          if (d === 0) throw new Error("divide by zero");
          v /= d;
        } else return v;
      }
    }

    function expr() {
      let v = term();
      for (;;) {
        ws();
        if (s[i] === "+") { i++; v += term(); }
        else if (s[i] === "-") { i++; v -= term(); }
        else return v;
      }
    }

    const val = expr();
    ws();
    if (i !== s.length) throw new Error("trailing input");
    return val;
  }

  function cEval() {
    if (!cExpr) return;
    try {
      if (!/^[0-9+\-*/.() ]+$/.test(cExpr)) throw new Error("bad characters");
      const val = evaluate(cExpr);
      if (!isFinite(val)) throw new Error("result not finite");
      cExpr = String(Math.round(val * 1e10) / 1e10);
    } catch (e) {
      cExpr = "";
    }
    cRender();
  }
  $$("#calcGrid button").forEach((b) =>
    (b.onclick = () => {
      const k = b.dataset.k;
      if (OP[k]) cExpr += OP[k];
      else if (k === "C") cExpr = "";
      else if (k === "⌫") cExpr = cExpr.slice(0, -1);
      else if (k === "=") return cEval();
      else cExpr += k;
      cRender();
    }));
  cRender();

  // ---------------------------------------------------- media player
  const vid = $("#vid");
  const fmt = (s) => isFinite(s)
    ? Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0") : "0:00";

  $("#vPick").onclick = () => $("#vidFile").click();
  $("#vidFile").onchange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    vid.src = URL.createObjectURL(f);
    vid.style.display = "block";
    $("#vidPh").style.display = "none";
    vid.play().catch(() => {});
  };
  $("#vPlay").onclick = () => {
    if (!vid.src) return $("#vidFile").click();
    vid.paused ? vid.play() : vid.pause();
  };
  $("#vBack").onclick = () => (vid.currentTime -= 10);
  $("#vFwd").onclick  = () => (vid.currentTime += 10);
  $("#vMute").onclick = () => { vid.muted = !vid.muted; $("#vMute").textContent = vid.muted ? "🔇" : "🔊"; };
  vid.ontimeupdate = () => {
    $("#vTime").textContent = fmt(vid.currentTime) + " / " + fmt(vid.duration);
    if (vid.duration) $("#vSeek").value = (vid.currentTime / vid.duration) * 1000;
  };
  vid.onplay = () => ($("#vPlay").textContent = "⏸");
  vid.onpause = () => ($("#vPlay").textContent = "▶");
  vid.onended = () => ($("#vPlay").textContent = "▶");
  $("#vSeek").oninput = (e) => { if (vid.duration) vid.currentTime = (e.target.value / 1000) * vid.duration; };

  // ---------------------------------------------------- to-do
  const TD_KEY = "ab_workhub_todo";
  let todos = [];
  try { todos = JSON.parse(localStorage.getItem(TD_KEY) || "[]"); } catch (e) {}

  function tdSave() {
    try { localStorage.setItem(TD_KEY, JSON.stringify(todos)); } catch (e) {}
  }
  function tdRender() {
    $("#tdList").innerHTML = todos.length
      ? todos.map((t, i) => `
        <li class="${t.done ? "done" : ""}">
          <input type="checkbox" class="cb" ${t.done ? "checked" : ""} data-i="${i}">
          <span data-t="${i}">${esc(t.text)}</span>
          <button data-d="${i}">✕</button>
        </li>`).join("")
      : '<li style="justify-content:center;color:var(--faint)">Nothing here yet — add a task above.</li>';

    const left = todos.filter((t) => !t.done).length;
    $("#tdCount").textContent = todos.length
      ? `${left} left of ${todos.length} task${todos.length > 1 ? "s" : ""}`
      : "";

    $$("#tdList .cb").forEach((c) => (c.onchange = () => {
      todos[+c.dataset.i].done = c.checked; tdSave(); tdRender();
    }));
    $$("#tdList [data-t]").forEach((s) => (s.onclick = () => {
      const i = +s.dataset.t; todos[i].done = !todos[i].done; tdSave(); tdRender();
    }));
    $$("#tdList [data-d]").forEach((b) => (b.onclick = () => {
      todos.splice(+b.dataset.d, 1); tdSave(); tdRender();
    }));
  }
  function tdAdd() {
    const v = $("#tdIn").value.trim();
    if (!v) return;
    todos.unshift({ text: v, done: false });
    $("#tdIn").value = ""; tdSave(); tdRender();
  }
  $("#tdAdd").onclick = tdAdd;
  $("#tdIn").addEventListener("keydown", (e) => { if (e.key === "Enter") tdAdd(); });
  tdRender();

  // ---------------------------------------------------- wallet demo
  let LS_ACCT = null;
  function loadWallet() {
    if (!ON_FLASK) return loadWalletLocal();
    api("/api/wallet").then(walletRender).catch(() => loadWalletLocal(true));
  }
  /* reach=true means we are on a real page but there is no API behind it,
     which is the case for the published static copy */
  function loadWalletLocal(reach) {
    if (reach) {
      $("#wMode").innerHTML = "&#9432; <b>Demo mode</b> - this copy is published as a plain website, " +
        "so transfers are kept in your browser and reset on reload.";
    }
    if (!LS_ACCT) {
      LS_ACCT = [
        { id: 1, name: "Demo User", email: "user1@example.com", balance: 12500 },
        { id: 2, name: "Wallet",    email: "user2@example.com", balance: 0 },
        { id: 3, name: "Alex",      email: "user3@example.com", balance: 4200 },
        { id: 4, name: "Sam",       email: "user4@example.com", balance: 3100 }
      ];
    }
    walletRender(LS_ACCT);
    $("#wHist").innerHTML = "<li style='color:var(--faint)'>Demo mode — history resets on reload.</li>";
  }

  function walletRender(accts) {
    $("#wAccts").innerHTML = accts.map((a) => `
      <div class="acct ${a.id === 1 ? "me" : ""}">
        <div class="av">${esc(a.name[0])}</div>
        <div><div class="nm">${esc(a.name)}</div><div class="em">${esc(a.email)}</div></div>
        <div class="bal">${money(a.balance)}</div>
      </div>`).join("");

    const opts = (sel) => accts.map((a) =>
      `<option value="${a.id}" ${String(a.id) === sel ? "selected" : ""}>${esc(a.name)}</option>`).join("");
    const f = $("#wFrom").value || "1", t = $("#wTo").value || "3";
    $("#wFrom").innerHTML = opts(f);
    $("#wTo").innerHTML = opts(t);
  }

  $("#wSend").onclick = async () => {
    const body = {
      from: +$("#wFrom").value, to: +$("#wTo").value,
      amount: parseFloat($("#wAmt").value), note: $("#wNote").value || "Transfer"
    };
    const msg = $("#wMsg");

    if (!ON_FLASK) {
      const a = LS_ACCT.find((x) => x.id === body.from);
      const b = LS_ACCT.find((x) => x.id === body.to);
      if (body.amount <= 0) { msg.className = "msg no"; msg.textContent = "Amount must be more than 0"; return; }
      if (a.id === b.id) { msg.className = "msg no"; msg.textContent = "Cannot send to yourself"; return; }
      if (a.balance < body.amount) { msg.className = "msg no"; msg.textContent = "Insufficient balance"; return; }
      a.balance -= body.amount; b.balance += body.amount;
      walletRender(LS_ACCT);
      msg.className = "msg ok"; msg.textContent = "Sent " + money(body.amount) + " to " + b.name;
      return;
    }

    try {
      const r = await post("/api/wallet/send", body);
      msg.className = r.ok ? "msg ok" : "msg no";
      msg.textContent = r.ok ? "✓ " + r.message : "✕ " + r.error;
      if (r.ok) {
        $("#wNote").value = "";
        await loadWallet();
        api("/api/wallet/history").then((h) => {
          $("#wHist").innerHTML = h.length
            ? h.map((t) => `<li><span>${esc(t.frm_name)} → ${esc(t.to_name)}
                 <span style="color:var(--faint)">· ${esc(t.note)}</span></span>
                 <span class="amt out">−${money(t.amount)}</span></li>`).join("")
            : "<li style='color:var(--faint)'>No transfers yet.</li>";
        });
      }
    } catch (e) {
      msg.className = "msg no";
      msg.textContent = "Backend not reachable — is app.py running?";
    }
  };

  $("#wReset").onclick = async () => {
    if (ON_FLASK) { try { await post("/api/wallet/reset"); } catch (e) {} }
    $("#wMsg").className = "msg";
    loadWallet();
    toast("Demo reset");
  };

  // ======================================================= CODE BROWSER
  function renderCodePicker() {
    const sel = $("#cbProj");
    if (!sel) return;                     // hidden in public mode
    const cats = CAT.categories.map((c) =>
      `<optgroup label="${esc(c.title)}">${
        c.projects.filter((p) => p.exists).map((p) =>
          `<option value="${p.id}">${esc(p.title)}</option>`).join("")
      }</optgroup>`).join("");
    sel.innerHTML = `<option value="">— choose a project —</option>` + cats;
  }

  function listMsg(t) { return `<div class="empty"><div class="e">📁</div>${t}</div>`; }

  async function openCode(p) {
    $("#cbFileBar").style.display = "none";
    $("#cbOut").innerHTML = listMsg("Reading…");
    try {
      const res = await api("/api/read?path=" + encodeURIComponent(p.subpath));

      // the project IS a single file (e.g. a one-page app) - show it directly
      if (res.type === "file") {
        $("#cbProj").value = p.id;
        $("#cbFile").innerHTML = `<option value="">${esc(res.name)}</option>`;
        $("#cbFileBar").style.display = "none";
        paintCode(res);
        return;
      }

      if (res.type !== "dir") {
        $("#cbOut").innerHTML = listMsg("That project has no readable folder.");
        return;
      }

      const files = res.items.filter((i) => !i.dir);
      $("#cbFile").innerHTML = `<option value="">— choose a file (${files.length}) —</option>` +
        files.map((f) => `<option value="${esc(f.name)}">${esc(f.name)} · ${f.kb} KB</option>`).join("");
      $("#cbFileBar").style.display = "flex";
      $("#cbProj").value = p.id;

      const start = p.entry && files.some((f) => f.name === p.entry)
        ? p.entry : (files[0] || {}).name;
      if (start) { $("#cbFile").value = start; showCode(start); }
      else $("#cbOut").innerHTML = listMsg("Folder is empty.");
    } catch (e) {
      $("#cbOut").innerHTML = listMsg("Could not read that project - is app.py running?");
    }
  }

  /* render one file payload that the API already returned */
  function paintCode(r) {
    if (r.type === "binary") {
      $("#cbOut").innerHTML = listMsg("Binary file - cannot display");
      $("#cbInfo").textContent = "";
      return;
    }
    if (!r.content || !r.content.trim()) {
      $("#cbOut").innerHTML =
        `<div class="empty"><div class="e">&#128196;</div>
           This file is empty on disk (0 bytes).</div>`;
      $("#cbInfo").textContent = `${r.name} · empty`;
      return;
    }
    $("#cbOut").innerHTML = `<pre class="code" id="codeBox">${highlight(r.content)}</pre>`;
    $("#cbInfo").textContent = `${r.name} · ${r.lines} lines · ${kbTxt(r.kb || 0)}`;
    $("#codeBox").dataset.raw = r.content;
  }

  async function showCode(name) {
    const p = ALL.find((x) => x.id === $("#cbProj").value);
    if (!p || !name) return;
    $("#cbOut").innerHTML = listMsg("Loading…");
    try {
      const full = p.subpath.replace(/[\\/]+$/, "") + "/" + name;
      const r = await api("/api/read?path=" + encodeURIComponent(full));
      paintCode(r);
    } catch (e) {
      $("#cbOut").innerHTML = listMsg("Could not read that file.");
    }
  }

  const KW = /\b(def|class|return|if|else|elif|for|while|import|from|as|try|except|finally|with|lambda|None|True|False|and|or|not|async|await|pass|raise|global|del|yield|const|let|var|function)\b/g;

  /* split a line into "code" and "comment", ignoring # inside strings */
  function splitComment(line) {
    let quote = null, i = 0;
    while (i < line.length) {
      const triple = line.slice(i, i + 3);
      if (quote) {
        if (line[i] === "\\") { i += 2; continue; }
        const qlen = quote.length;                 // read BEFORE clearing
        if (triple === quote || (qlen === 1 && line[i] === quote)) {
          quote = null;
          i += qlen === 1 ? 1 : 3;
          continue;
        }
      } else if (triple === '"""' || triple === "'''") {
        quote = triple; i += 3; continue;
      } else if (line[i] === '"' || line[i] === "'") {
        quote = line[i]; i++; continue;
      } else if (line[i] === "#" || (line[i] === "/" && line[i + 1] === "/")) {
        return [line.slice(0, i), line.slice(i)];
      }
      i++;
    }
    return [line, ""];
  }

  /* highlight one string-free chunk; strings are parked behind a
     digit-free marker so the keyword / number regexes can never eat them */
  function hiCode(src) {
    const store = [];
    let s = esc(src).replace(
      /"""[\s\S]*?"""|''[\s\S]*?''|"[^"\n]*"|'[^'\n]*'/g,
      (m) => { store.push(m); return "\uE000".repeat(store.length) + "\uE001"; }
    );
    s = s.replace(KW, '<span class="kw">$1</span>')
         .replace(/\b(\d+\.?\d*)\b/g, '<span class="num">$1</span>')
         .replace(/\uE000+\uE001+/g, (m) => {
           const n = (m.match(/\uE000/g) || []).length;
           return '<span class="str">' + store[n - 1] + "</span>";
         });
    return s;
  }

  function highlight(code) {
    return String(code).split("\n").map((line) => {
      const [body, note] = splitComment(line);
      return hiCode(body) + (note ? '<span class="com">' + esc(note) + "</span>" : "");
    }).join("\n");
  }

  $("#cbOpen").onclick = () => {
    const p = ALL.find((x) => x.id === $("#cbProj").value);
    if (!p) return toast("Pick a project first");
    if (!p.exists) return toast("Folder not found on disk");
    openCode(p);
  };
  $("#cbProj").onchange = () => { $("#cbFileBar").style.display = "none"; };
  $("#cbFile").onchange = (e) => e.target.value && showCode(e.target.value);
  $("#cbCopy").onclick = () => {
    const box = $("#codeBox");
    if (!box) return toast("Nothing to copy");
    navigator.clipboard.writeText(box.dataset.raw || "")
      .then(() => toast("Code copied ✓"))
      .catch(() => toast("Copy failed"));
  };

  // ======================================================= SKILLS
  function renderSkills() {
    const counts = {};
    ALL.forEach((p) => p.tech.forEach((t) => (counts[t] = (counts[t] || 0) + 1)));
    const list = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const max = list.length ? list[0][1] : 1;

    $("#skillGrid").innerHTML = list.map(([name, n]) => `
      <div class="card skill-card" data-tech="${esc(name)}"
           title="Show the ${n} project${n > 1 ? "s" : ""} that use ${esc(name)}">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <div class="card-ico">${esc(name[0].toUpperCase())}</div>
          <div><h3>${esc(name)}</h3><div class="cat">${n} project${n > 1 ? "s" : ""}</div></div>
        </div>
        <div class="bar-wrap"><div class="bar-fill" style="width:${(n / max) * 100}%"></div></div>
      </div>`).join("");

    /* a skill card is a shortcut: jump to Projects, pre-filtered by that tech */
    $$("#skillGrid .skill-card").forEach((el) =>
      (el.onclick = () => {
        activeTech = activeTech === el.dataset.tech ? "" : el.dataset.tech;
        activeFilter = "all";
        show("projects");
        renderFilters();
        renderProjects();
        toast(activeTech
          ? "Filtered by " + activeTech
          : "Skill filter cleared");
      }));
  }

  function renderTimeline() {
    const list = ALL.filter((p) => p.date).sort((a, b) => b.date.localeCompare(a.date)).slice(0, 14);
    $("#timeline").innerHTML = list.map((p) => `
      <div class="tl-item" data-id="${p.id}" title="Open ${esc(p.title)}">
        <div class="tl-date">${p.date}</div>
        <div class="tl-txt"><b>${esc(p.title)}</b>
          <span style="color:var(--faint)"> — ${esc(p.categoryTitle)}</span></div>
      </div>`).join("");
    $$("#timeline .tl-item").forEach((el) =>
      (el.onclick = () => openProject(el.dataset.id)));
  }

  // ======================================================= misc
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove("show"), 2400);
  }

  $("#rescan").onclick = async () => {
    if (!ON_FLASK) return toast("Rescan needs the Flask app running");
    toast("Scanning your folders…");
    try {
      const r = await post("/api/rescan");
      toast(r.ok ? "✓ Rescan complete" : "Rescan finished with warnings");
      if (r.ok) { const d = await api("/api/projects"); CAT = d;
        ALL = []; d.categories.forEach((c) => c.projects.forEach((p) => {
          p.categoryId = c.id; p.categoryTitle = c.title; p.color = c.color; ALL.push(p); }));
        buildUI(); show("about"); }
    } catch (e) { toast("Rescan failed"); }
  };

  // ======================================================= theme
  const THEME_KEY = "ab_workhub_theme";
  const themeNow = () => document.documentElement.dataset.theme || "dark";

  function applyTheme(t) {
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
    const lbl = $("#themeTxt");
    if (lbl) lbl.textContent = t === "light" ? "Dark" : "Light";
    const ico = $("#themeBtn .t-ico");
    if (ico) ico.textContent = t === "light" ? "◑" : "◐";
  }
  function toggleTheme() {
    const next = themeNow() === "light" ? "dark" : "light";
    applyTheme(next);
    toast(next === "light" ? "Light theme on" : "Dark theme on");
  }
  $("#themeBtn").onclick = toggleTheme;
  applyTheme(themeNow());

  // ======================================================= toolbar
  $("#searchClear").onclick = () => {
    $("#search").value = "";
    renderProjects();
    $("#search").focus();
  };
  $("#sortSel").onchange = renderProjects;

  /* "Surprise me" opens something from whatever is on screen right now, so a
     filtered or searched list stays consistent with what the click offers */
  function openRandom() {
    const shown = $$("#allProjects .card[data-id]").map((el) => el.dataset.id);
    const pool = shown.length ? shown : ALL.map((p) => p.id);
    if (!pool.length) return toast("Nothing to open right now");
    openProject(pool[Math.floor(Math.random() * pool.length)]);
  }
  $("#randBtn").onclick = openRandom;

  const toTop = $("#toTop");
  toTop.onclick = () => window.scrollTo({ top: 0, behavior: "smooth" });
  window.addEventListener("scroll", () =>
    toTop.classList.toggle("on", window.scrollY > 420), { passive: true });

  // ======================================================= keyboard
  const SHORTCUTS = [
    ["/", "Jump straight to search"],
    ["t", "Switch dark / light theme"],
    ["r", "Open a random project"],
    ["?", "Show this help"],
    ["Esc", "Close the open dialog"]
  ];

  function openShortcuts() {
    $("#modalBox").innerHTML =
      `<button class="modal-close" id="mClose">&#10005;</button>
       <h2>Keyboard shortcuts</h2>
       <div class="sub">Drive the whole hub without touching the mouse.</div>
       <div class="kbd-list">${SHORTCUTS.map(([k, d]) =>
         `<div class="kbd-row"><span class="kd">${esc(d)}</span>
            <span class="kk"><kbd>${esc(k)}</kbd></span></div>`).join("")}</div>`;
    $("#modal").classList.add("open");
    $("#mClose").onclick = closeModal;
  }
  $("#keysBtn").onclick = openShortcuts;

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return closeModal();
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (e.key === "/") { e.preventDefault(); show("projects"); $("#search").focus(); return; }
    if (e.key === "?") { e.preventDefault(); openShortcuts(); return; }
    const k = e.key.toLowerCase();
    if (k === "t") return toggleTheme();
    if (k === "r") { e.preventDefault(); openRandom(); }
  });

  // ======================================================= deep links
  function applyHash() {
    const h = readHash();
    if (!h) return;
    if (h.kind === "p") { show("projects", false); openProject(h.arg, false); return; }
    if (h.kind === "v") show(h.arg, false);
  }
  window.addEventListener("popstate", applyHash);

  loadCatalog().then(applyHash);
})();
