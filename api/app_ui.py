def render_app_ui() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Strategy OS</title>
  <style>
    :root {
      --bg: #0a1016;
      --surface: rgba(16, 24, 33, 0.9);
      --surface-2: rgba(21, 31, 42, 0.84);
      --ink: #eef3f8;
      --muted: #9aa8b8;
      --accent: #ff6b57;
      --accent-2: #ff8c6b;
      --line: rgba(158, 178, 198, 0.16);
      --shadow: 0 20px 52px rgba(0, 0, 0, 0.34);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(255, 107, 87, 0.18), transparent 24%),
        radial-gradient(circle at left 18%, rgba(76, 132, 255, 0.12), transparent 26%),
        linear-gradient(180deg, #0f1721 0%, var(--bg) 100%);
    }

    .shell {
      width: min(1320px, calc(100vw - 32px));
      margin: 28px auto 40px;
    }

    .hero, .section {
      border-radius: 28px;
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .hero {
      padding: 18px 22px;
    }

    h1 {
      margin: 0;
      line-height: 1;
      letter-spacing: -0.04em;
      font-size: clamp(1.5rem, 3vw, 2.4rem);
    }

    .button-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      border-radius: 14px;
      text-decoration: none;
      font: 700 0.88rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
      color: white;
      background: linear-gradient(135deg, var(--accent), #d44731);
      box-shadow: 0 10px 24px rgba(255, 107, 87, 0.22);
    }

    .button-link.secondary {
      color: var(--ink);
      background: rgba(30, 43, 57, 0.92);
      border: 1px solid var(--line);
      box-shadow: none;
    }

    .button-link.logout {
      cursor: pointer;
    }

    .nav {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 18px 0;
    }

    .nav a {
      text-decoration: none;
      color: var(--ink);
      background: rgba(24, 35, 47, 0.82);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 10px 14px;
      font: 700 0.88rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .section {
      padding: 20px;
    }

    .section form {
      margin-top: 16px;
    }

    .footer {
      margin-top: 18px;
      padding: 18px 22px;
    }

    .footer-copy {
      margin: 0;
      color: var(--muted);
      font: 500 0.94rem/1.6 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .footer-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
    }

    .footer-actions .button-link {
      width: auto;
    }

    .section h2 {
      margin: 0 0 8px;
      font-size: 1.45rem;
    }

    .section p {
      margin: 0 0 14px;
      color: var(--muted);
      font: 500 0.95rem/1.6 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .controls.one-col {
      grid-template-columns: 1fr;
    }

    .full {
      grid-column: 1 / -1;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field-label {
      color: var(--muted);
      font: 700 0.78rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .checkbox-inline {
      display: inline-flex;
      align-items: center;
      justify-content: flex-start;
      gap: 10px;
      color: var(--ink);
      font: 600 0.92rem/1.2 "Helvetica Neue", Helvetica, Arial, sans-serif;
      margin-top: 6px;
    }

    .checkbox-inline input {
      width: auto;
      margin: 0;
    }

    input, textarea, select, button {
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      font-size: 0.95rem;
    }

    input, textarea, select {
      border: 1px solid var(--line);
      color: var(--ink);
      background: rgba(11, 18, 26, 0.92);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    select {
      cursor: pointer;
    }

    select option {
      background: #0f1721;
      color: var(--ink);
    }

    input::placeholder, textarea::placeholder {
      color: #728196;
    }

    input:focus, textarea:focus, select:focus {
      outline: none;
      border-color: rgba(255, 107, 87, 0.54);
      box-shadow: 0 0 0 3px rgba(255, 107, 87, 0.12);
    }

    textarea {
      min-height: 132px;
      resize: vertical;
    }

    button {
      border: none;
      cursor: pointer;
      color: white;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), #d44731);
      box-shadow: 0 10px 24px rgba(255, 107, 87, 0.22);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      padding: 11px 14px;
      border-radius: 13px;
    }

    .controls button {
      margin-top: 8px;
    }

    .status {
      min-height: 22px;
      margin-top: 18px;
      color: var(--muted);
      font: 500 0.92rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .output {
      margin-top: 16px;
      border-radius: 18px;
      padding: 14px;
      background: var(--surface-2);
      border: 1px solid rgba(158, 178, 198, 0.1);
      min-height: 76px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .cards {
      display: grid;
      gap: 12px;
    }

    .card {
      border-radius: 18px;
      padding: 16px;
      background: rgba(12, 19, 28, 0.88);
      border: 1px solid rgba(158, 178, 198, 0.08);
    }

    .tag {
      display: inline-flex;
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(255, 107, 87, 0.14);
      color: #ffb19f;
      font: 700 0.76rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .title {
      margin: 10px 0 6px;
      font-size: 1.06rem;
      line-height: 1.3;
    }

    .meta {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.5;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
    }

    .stat {
      padding: 10px;
      border-radius: 14px;
      background: rgba(22, 33, 45, 0.92);
      border: 1px solid rgba(158, 178, 198, 0.07);
    }

    .stat-label {
      display: block;
      color: var(--muted);
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .stat-value {
      display: block;
      margin-top: 6px;
      font-weight: 700;
    }

    .line {
      margin-top: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.92rem;
      color: var(--muted);
    }

    .link {
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }

    .checkboxes {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .checkbox-row {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      padding: 12px;
      border-radius: 14px;
      background: rgba(22, 33, 45, 0.78);
      border: 1px solid rgba(158, 178, 198, 0.07);
    }

    .checkbox-row input {
      width: auto;
      margin-top: 2px;
    }

    .badge {
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 20px;
      vertical-align: middle;
      margin-left: 6px;
    }

    .badge-multi {
      background: rgba(99, 179, 237, 0.15);
      color: #63b3ed;
      border: 1px solid rgba(99, 179, 237, 0.3);
    }

    .subtopic-list {
      margin: 6px 0 0 0;
      padding-left: 16px;
      list-style: disc;
    }

    .subtopic-list li {
      font-size: 0.82rem;
      color: rgba(210, 225, 240, 0.65);
      line-height: 1.5;
      margin-bottom: 2px;
    }

    .btn-icon {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 4px;
      color: rgba(210,225,240,0.5);
      cursor: pointer;
      font-size: 0.78rem;
      line-height: 1;
      padding: 3px 7px;
    }
    .btn-icon:hover { background: rgba(255,255,255,0.08); color: rgba(210,225,240,0.9); }
    .btn-icon.btn-danger { border-color: rgba(245,101,101,0.25); color: rgba(245,101,101,0.55); }
    .btn-icon.btn-danger:hover { background: rgba(245,101,101,0.1); color: rgba(245,101,101,0.9); }
    .btn-add {
      background: transparent;
      border: 1px dashed rgba(99,179,237,0.3);
      border-radius: 4px;
      color: rgba(99,179,237,0.65);
      cursor: pointer;
      font-size: 0.78rem;
      padding: 3px 10px;
    }
    .btn-add:hover { background: rgba(99,179,237,0.08); }
    .tp-sec-title, .tp-sub-title, .tp-bullet-input {
      background: transparent;
      border: none;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      color: inherit;
      font-family: inherit;
      outline: none;
      padding: 2px 4px;
      width: 100%;
    }
    .tp-sec-title:focus, .tp-sub-title:focus, .tp-bullet-input:focus {
      border-bottom-color: rgba(99,179,237,0.5);
    }

    .mono {
      white-space: pre-wrap;
      font: 500 0.9rem/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    #research, #create, #hooks-talking-points {
      grid-column: 1 / -1;
    }

    .progress-log {
      margin-top: 10px;
      height: 180px;
      overflow: auto;
      white-space: pre-wrap;
      font: 500 0.86rem/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    .summary-list {
      margin: 0;
      padding-left: 18px;
      line-height: 1.7;
    }

    @media (max-width: 980px) {
      .grid, .controls, .stats {
        grid-template-columns: 1fr;
      }

      .section {
        padding: 18px;
      }
    }

    @media (max-width: 720px) {
      .shell {
        width: min(1320px, calc(100vw - 20px));
        margin: 18px auto 28px;
      }

      .hero {
        padding: 16px 18px;
      }

      .nav {
        gap: 8px;
        margin: 14px 0;
      }

      .nav a {
        padding: 9px 12px;
        font-size: 0.82rem;
      }

      .section {
        padding: 16px;
        border-radius: 22px;
      }

      .section h2 {
        font-size: 1.25rem;
      }

      .section p {
        margin-bottom: 16px;
        font-size: 0.92rem;
      }

      input, textarea, select, button {
        font-size: 0.94rem;
      }

      textarea {
        min-height: 110px;
      }

      .footer-actions {
        flex-direction: column;
      }

      .button-link {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>YouTube Strategy OS</h1>
    </section>

    <nav class="nav">
      <a href="#trends">Trends</a>
      <a href="#outlier">Outlier</a>
      <a href="#research">Titles &amp; Topics</a>
      <a href="#create">Create</a>
    </nav>

    <section class="grid">
      <section class="section" id="trends">
        <h2>Trend Discovery</h2>
        <p>Mine recent tech videos and surface the AI terms rising fastest on YouTube right now.</p>
        <form id="trend-form" class="controls">
          <label class="field full">
            <span class="field-label">Seed Topics</span>
            <textarea id="trend-seeds" placeholder="artificial intelligence, ai agents, llm, coding, automation">artificial intelligence, ai agents, llm, coding, developer tools, automation</textarea>
          </label>
          <label class="field">
            <span class="field-label">Lookback Days</span>
            <input id="trend-lookback" type="number" min="1" max="90" value="14" placeholder="Days">
          </label>
          <label class="field">
            <span class="field-label">Videos Per Seed</span>
            <input id="trend-limit" type="number" min="5" max="50" value="15" placeholder="Videos per seed">
          </label>
          <label class="field">
            <span class="field-label">Max Terms</span>
            <input id="trend-max-terms" type="number" min="3" max="25" value="12" placeholder="Max terms">
          </label>
          <label class="checkbox-inline"><input id="trend-ai-only" type="checkbox" checked><span>Only show AI-related terms</span></label>
          <button class="full" type="submit">Run Trend Discovery</button>
        </form>
        <div class="status" id="trend-status">Use this to spot rising AI phrases before drilling into outliers and scripts.</div>
        <div class="output" id="trend-output"></div>
      </section>

      <section class="section" id="outlier">
        <h2>Outlier Search</h2>
        <p>Single-term search with optional AI insights. Select results here and reuse them in downstream workflows.</p>
        <form id="outlier-form" class="controls">
          <label class="field full">
            <span class="field-label">Load Past Run</span>
            <select id="outlier-past-select">
              <option value="">— Select a past run —</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">Topic</span>
            <input id="outlier-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <label class="field">
            <span class="field-label">Minimum Outliers</span>
            <input id="outlier-limit" type="number" min="1" max="20" value="10" placeholder="Limit">
          </label>
          <label class="field">
            <span class="field-label">Max Subscribers (Best Effort)</span>
            <input id="outlier-max-subscribers" type="number" min="0" step="1000" value="200000" placeholder="Subscriber cap">
          </label>
          <label class="checkbox-inline full"><input id="outlier-insights" type="checkbox" checked><span>Include AI insights</span></label>
          <button class="full" type="submit">Run New Outlier Search</button>
        </form>
        <div class="status" id="outlier-status">Load a past run or run a new search. Selected outliers flow into Titles &amp; Topics and Create.</div>
        <div class="output" id="outlier-output"></div>
      </section>

      <section class="section" id="discovery" style="display:none">
        <h2>Discovery</h2>
        <p>Multi-term search that collates outliers across several topics into one report. Or load a past outlier run directly into session.</p>
        <form id="discovery-form" class="controls one-col">
          <label class="field full" style="margin-bottom:6px;">
            <span class="field-label">Load Past Outlier Run into Session</span>
            <select id="discovery-past-select">
              <option value="">— Select a past run —</option>
            </select>
          </label>
          <textarea id="discovery-terms" placeholder="claude code, cursor ai, github copilot">claude code, cursor ai</textarea>
          <button type="submit">Run Multi-Term Discovery</button>
        </form>
        <div class="status" id="discovery-status"></div>
        <div class="output" id="discovery-output"></div>
      </section>

      <section class="section" id="theme" style="display:none">
        <h2>Theme</h2>
        <p>Find recurring patterns, title moves, and audience intent across the latest outlier set.</p>
        <form id="theme-form" class="controls">
          <label class="field full">
            <span class="field-label">Topic</span>
            <input id="theme-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <button class="full" type="submit">Analyze Theme</button>
        </form>
        <div class="output" id="theme-past-run" style="margin-top:12px;"></div>
        <div class="status" id="theme-status"></div>
        <div class="output" id="theme-output"></div>
      </section>

      <section class="section" id="research">
        <h2>Titles &amp; Topics</h2>
        <p>Get the best video titles and topics from what's already working. Selects an outlier set as the primary source — notes and links are optional.</p>
        <form id="research-form" class="controls">
          <label class="field full">
            <span class="field-label">Outlier Set (Primary Source)</span>
            <select id="research-outlier-select">
              <option value="current">Current session outliers</option>
            </select>
          </label>
          <label class="field full">
            <span class="field-label">My Notes (Optional)</span>
            <textarea id="research-notes" placeholder="Angles, themes, or context to consider alongside the outliers..."></textarea>
          </label>
          <label class="field full">
            <span class="field-label">Extra Links (Optional)</span>
            <textarea id="research-sources" placeholder="Paste URLs you want considered (one per line)"></textarea>
          </label>
          <button class="full" type="submit">Get Titles &amp; Topics</button>
        </form>
        <div class="status" id="research-status">Select an outlier set above. The AI will surface the best titles and topics from what's already working.</div>
        <div class="output" id="research-output"></div>
      </section>

      <section class="section" id="hooks-talking-points">
        <h2>Hooks &amp; Talking Points</h2>
        <p>Select a hook, edit the talking points outline, and set an outro before creating the script.</p>
        <div class="controls" style="margin-bottom:8px">
          <label class="field full">
            <span class="field-label">Titles &amp; Topics (from research)</span>
            <select id="htp-past-research-select">
              <option value="">— Use current session —</option>
            </select>
          </label>
          <div id="htp-research-summary" class="meta" style="margin-top:6px;padding:10px;border-radius:8px;background:rgba(22,33,45,0.6);border:1px solid rgba(158,178,198,0.1);display:none"></div>
        </div>
        <form id="htp-form" class="controls">
          <label class="field full">
            <span class="field-label">Custom Title Override (optional)</span>
            <input id="htp-custom-title" type="text" placeholder="Leave blank to use the selected title from Titles &amp; Topics">
          </label>
          <label class="field full">
            <span class="field-label">Extra Topics / Notes (optional)</span>
            <textarea id="htp-custom-notes" placeholder="Additional topics, context, or talking points you want included..."></textarea>
          </label>
          <button class="full" type="submit">Generate Hooks &amp; Talking Points</button>
        </form>
        <div class="status" id="htp-status">Run Titles &amp; Topics first, then come here to generate hooks and a talking points outline.</div>
        <div class="output" id="htp-output"></div>
      </section>

      <section class="section" id="create">
        <h2>Create Script</h2>
        <p>Runs the full creation pipeline. Uses the selected hook and talking points from the step above.</p>
        <form id="create-form" class="controls">
          <label class="field">
            <span class="field-label">Duration (Minutes)</span>
            <input id="create-duration" type="number" min="1" max="60" value="11" placeholder="Duration">
          </label>
          <label class="field">
            <span class="field-label">Hooks &amp; Talking Points</span>
            <select id="create-htp-select">
              <option value="">— Use current session —</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">Videos To Analyze</span>
            <input id="create-top-n" type="number" min="1" max="30" value="10" placeholder="Videos to analyze">
          </label>
          <label class="field full">
            <span class="field-label">Notes</span>
            <textarea id="create-notes" class="full" placeholder="Your rough notes">Target AI enthusiasts and business leaders. Explain why this matters now, where teams waste time today, and what practical first steps look like.</textarea>
          </label>
          <button class="full" type="submit">Create Script</button>
        </form>
        <div class="status" id="create-status"></div>
        <div class="output" id="create-output"></div>
      </section>
    </section>

    <section class="hero footer">
      <p class="footer-copy">
        This app fronts the current workflow: trend discovery, outlier search, titles &amp; topics, and create.
        Run an Outlier search first — selected outliers flow into Titles &amp; Topics and Create.
      </p>
      <div class="footer-actions">
        <a class="button-link secondary" href="/docs">API Docs</a>
        <a class="button-link secondary" href="/api">Raw API Index</a>
        <a class="button-link secondary" href="/home">Overview</a>
        <button class="button-link secondary logout" id="logout-button" type="button">Logout</button>
      </div>
    </section>
  </main>

  <script>
    const state = {
      latestOutliers: [],
      latestTheme: null,
      latestResearch: null,
      selectedResearchTitle: "",
      selectedResearchTopics: new Set(),
      selectedThumbnail: null,
      latestHooksTalkingPoints: null,
      htpTitle: "",
      selectedHookScript: "",
      editedTalkingPoints: null,
      editedOutro: "",
      selectedUrls: new Set(),
      pastResearch: [],
      pastHooksTp: [],
      activeTrendJobId: null,
      trendPollTimer: null,
      activeOutlierJobId: null,
      outlierPollTimer: null,
      activeDiscoveryJobId: null,
      discoveryPollTimer: null,
      activeCreateJobId: null,
      createPollTimer: null,
      pastOutlierJobs: [],
      pastDiscoveryJobs: [],
      pastThemes: []
    };

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function formatNumber(value) {
      return new Intl.NumberFormat().format(value || 0);
    }

    function selectedOutliers() {
      return state.latestOutliers.filter((item) => state.selectedUrls.has(item.url));
    }

    async function logout() {
      try {
        await fetch("/api/v1/auth/logout", { method: "POST" });
      } finally {
        window.location.href = "/login";
      }
    }

    function syncTopicFields(topic) {
      const input = document.getElementById("theme-topic");
      if (input) input.value = topic;
    }

    async function postJson(url, payload, timeoutMs = 300000) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal
        });
        if (response.status === 401) {
          window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname + window.location.search);
          throw new Error("Authentication required");
        }
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || data.error || "Request failed");
        }
        return data;
      } finally {
        clearTimeout(timer);
      }
    }

    async function getJson(url, timeoutMs = 300000) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (response.status === 401) {
          window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname + window.location.search);
          throw new Error("Authentication required");
        }
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || data.error || "Request failed");
        }
        return data;
      } finally {
        clearTimeout(timer);
      }
    }

    function setStatus(id, text) {
      document.getElementById(id).textContent = text;
    }

    function setOutputHtml(id, html) {
      document.getElementById(id).innerHTML = html;
    }

    function renderOutlierCards(items) {
      if (!items || !items.length) {
        return '<p class="meta">No outliers returned.</p>';
      }

      const selected = state.selectedUrls;
      return `
        <div class="cards">
          <div class="meta">Select rows to reuse them in Angles and Create.</div>
          <div class="checkboxes">
            ${items.map((item) => `
              <label class="checkbox-row">
                <input type="checkbox" data-url="${escapeHtml(item.url)}" ${selected.has(item.url) ? "checked" : ""}>
                <div>
                  <span class="tag">${item.ratio.toFixed(2)}x outlier</span>
                  <h3 class="title"><a class="link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></h3>
                  <p class="meta">${escapeHtml(item.channel || "Unknown channel")}</p>
                  <div class="stats">
                    <div class="stat"><span class="stat-label">Views</span><span class="stat-value">${formatNumber(item.views)}</span></div>
                    <div class="stat"><span class="stat-label">Median</span><span class="stat-value">${formatNumber(Math.round(item.median_views || 0))}</span></div>
                    <div class="stat"><span class="stat-label">Subscribers</span><span class="stat-value">${item.subscribers ? formatNumber(item.subscribers) : "Unavailable"}</span></div>
                  </div>
                </div>
              </label>
            `).join("")}
          </div>
        </div>
      `;
    }

    function renderOutlierProgress(logs) {
      const logLines = logs && logs.length
        ? [...logs].reverse().map((line) => escapeHtml(line)).join("\\n")
        : "Waiting for first progress update...";

      return `
        <div class="cards">
          <div class="card">
            <span class="tag">Live Progress</span>
            <div class="progress-log">${logLines}</div>
          </div>
        </div>
      `;
    }

    function stopOutlierPolling() {
      if (state.outlierPollTimer) {
        clearInterval(state.outlierPollTimer);
        state.outlierPollTimer = null;
      }
    }

    function stopTrendPolling() {
      if (state.trendPollTimer) {
        clearInterval(state.trendPollTimer);
        state.trendPollTimer = null;
      }
    }

    function stopDiscoveryPolling() {
      if (state.discoveryPollTimer) {
        clearInterval(state.discoveryPollTimer);
        state.discoveryPollTimer = null;
      }
    }

    function stopCreatePolling() {
      if (state.createPollTimer) {
        clearInterval(state.createPollTimer);
        state.createPollTimer = null;
      }
    }

    function renderCreateProgress(logs) {
      const logLines = logs && logs.length
        ? [...logs].reverse().map((line) => escapeHtml(line)).join("\\n")
        : "Waiting for first progress update...";

      return `
        <div class="cards">
          <div class="card">
            <span class="tag">Live Progress</span>
            <div class="progress-log">${logLines}</div>
          </div>
        </div>
      `;
    }

    async function pollOutlierJob(jobId) {
      try {
        const data = await getJson(`/api/v1/app/outlier/jobs/${encodeURIComponent(jobId)}`, 90000);
        setOutputHtml("outlier-output", renderOutlierProgress(data.logs || []));

        if (data.status === "completed") {
          stopOutlierPolling();
          state.activeOutlierJobId = null;
          state.latestOutliers = data.result?.results || [];
          state.selectedUrls = new Set(state.latestOutliers.map((item) => item.url));
          setStatus("outlier-status", `Loaded ${data.result?.count || 0} outliers for "${data.query}".`);
          setOutputHtml("outlier-output", renderOutlierCards(state.latestOutliers));
          // Refresh past-run dropdowns to include this new run
          loadPastRuns();
          return;
        }

        if (data.status === "failed") {
          stopOutlierPolling();
          state.activeOutlierJobId = null;
          setStatus("outlier-status", data.error || "Outlier search failed.");
          setOutputHtml("outlier-output", renderOutlierProgress(data.logs || []));
        }
      } catch (error) {
        stopOutlierPolling();
        state.activeOutlierJobId = null;
        setStatus("outlier-status", error.message || "Progress polling failed.");
      }
    }

    function renderTrendResult(result) {
      const terms = result?.terms || [];
      if (!terms.length) {
        return '<p class="meta">No AI trend terms were ranked from the recent video sample.</p>';
      }
      return `
        <div class="cards">
          <div class="meta">Videos analyzed: ${formatNumber(result.videos_analyzed || 0)} | Unique channels: ${formatNumber(result.unique_channels || 0)}</div>
          ${terms.map((item) => `
            <div class="card">
              <span class="tag">${escapeHtml(item.momentum || "trend")} · ${escapeHtml(String(item.trend_score || 0))}</span>
              <h3 class="title">${escapeHtml(item.term)}</h3>
              <div class="stats">
                <div class="stat"><span class="stat-label">Mentions</span><span class="stat-value">${formatNumber(item.mentions || 0)}</span></div>
                <div class="stat"><span class="stat-label">Channels</span><span class="stat-value">${formatNumber(item.distinct_channels || 0)}</span></div>
                <div class="stat"><span class="stat-label">Views/Day</span><span class="stat-value">${formatNumber(Math.round(item.avg_views_per_day || 0))}</span></div>
              </div>
              ${item.sample_videos?.length ? `
                <div class="checkboxes">
                  ${item.sample_videos.map((video) => `
                    <div class="checkbox-row">
                      <div>
                        <h3 class="title"><a class="link" href="${escapeHtml(video.url)}" target="_blank" rel="noreferrer">${escapeHtml(video.title || "Video")}</a></h3>
                        <p class="meta">${escapeHtml(video.channel || "Unknown channel")} · ${escapeHtml(video.upload_date || "Unknown date")} · ${formatNumber(video.views || 0)} views</p>
                      </div>
                    </div>
                  `).join("")}
                </div>
              ` : ""}
            </div>
          `).join("")}
        </div>
      `;
    }

    function renderTrendProgress(logs) {
      const logLines = logs && logs.length
        ? [...logs].reverse().map((line) => escapeHtml(line)).join("\\n")
        : "Waiting for first progress update...";

      return `
        <div class="cards">
          <div class="card">
            <span class="tag">Live Progress</span>
            <div class="progress-log">${logLines}</div>
          </div>
        </div>
      `;
    }

    async function pollTrendJob(jobId) {
      try {
        const data = await getJson(`/api/v1/app/trends/jobs/${encodeURIComponent(jobId)}`, 90000);
        setOutputHtml("trend-output", renderTrendProgress(data.logs || []));

        if (data.status === "completed") {
          stopTrendPolling();
          state.activeTrendJobId = null;
          setStatus("trend-status", `Trend discovery ranked ${(data.result?.terms || []).length} AI term(s).`);
          setOutputHtml("trend-output", renderTrendResult(data.result || {}));
          return;
        }

        if (data.status === "failed") {
          stopTrendPolling();
          state.activeTrendJobId = null;
          setStatus("trend-status", data.error || "Trend discovery failed.");
          setOutputHtml("trend-output", renderTrendProgress(data.logs || []));
        }
      } catch (error) {
        stopTrendPolling();
        state.activeTrendJobId = null;
        setStatus("trend-status", error.message || "Trend polling failed.");
      }
    }

    function renderDiscovery(items, reportName) {
      if (!items || !items.length) {
        return '<p class="meta">No discovery results returned.</p>';
      }
      const selected = state.selectedUrls;
      return `
        <div class="cards">
          <div class="meta">Select rows to reuse them in Titles &amp; Topics and Create. Report: ${escapeHtml(reportName || "N/A")} | Results: ${items.length}</div>
          <div class="checkboxes">
            ${items.map((item) => `
              <label class="checkbox-row">
                <input type="checkbox" data-url="${escapeHtml(item.url || '')}" ${selected.has(item.url) ? "checked" : ""}>
                <div>
                  <span class="tag">${(item.ratio || 0).toFixed(2)}x outlier</span>
                  <h3 class="title"><a class="link" href="${escapeHtml(item.url || '#')}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></h3>
                  <p class="meta">${escapeHtml(item.channel || "Unknown channel")}</p>
                  <div class="stats">
                    <div class="stat"><span class="stat-label">Views</span><span class="stat-value">${formatNumber(item.views)}</span></div>
                    <div class="stat"><span class="stat-label">Median</span><span class="stat-value">${formatNumber(Math.round(item.median_views || 0))}</span></div>
                    <div class="stat"><span class="stat-label">Subscribers</span><span class="stat-value">${item.subscribers ? formatNumber(item.subscribers) : "Unavailable"}</span></div>
                  </div>
                </div>
              </label>
            `).join("")}
          </div>
        </div>
      `;
    }

    function renderDiscoveryProgress(logs) {
      const logLines = logs && logs.length
        ? [...logs].reverse().map((line) => escapeHtml(line)).join("\\n")
        : "Waiting for first progress update...";

      return `
        <div class="cards">
          <div class="card">
            <span class="tag">Live Progress</span>
            <div class="progress-log">${logLines}</div>
          </div>
        </div>
      `;
    }

    async function pollDiscoveryJob(jobId) {
      try {
        const data = await getJson(`/api/v1/app/discovery/jobs/${encodeURIComponent(jobId)}`, 90000);
        setOutputHtml("discovery-output", renderDiscoveryProgress(data.logs || []));

        if (data.status === "completed") {
          stopDiscoveryPolling();
          state.activeDiscoveryJobId = null;
          const results = data.result?.results || [];
          // Store in latestOutliers so they flow to Titles & Topics and Create
          state.latestOutliers = results;
          state.selectedUrls = new Set(results.map((item) => item.url));
          setStatus("discovery-status", `Loaded ${data.result?.count || 0} discovery results. Select rows to use in Titles &amp; Topics and Create.`);
          setOutputHtml("discovery-output", renderDiscovery(results, data.result?.report_name));
          // Refresh dropdowns
          loadPastRuns();
          return;
        }

        if (data.status === "failed") {
          stopDiscoveryPolling();
          state.activeDiscoveryJobId = null;
          setStatus("discovery-status", data.error || "Discovery failed.");
          setOutputHtml("discovery-output", renderDiscoveryProgress(data.logs || []));
        }
      } catch (error) {
        stopDiscoveryPolling();
        state.activeDiscoveryJobId = null;
        setStatus("discovery-status", error.message || "Discovery polling failed.");
      }
    }

    async function pollCreateJob(jobId) {
      try {
        const data = await getJson(`/api/v1/app/create/jobs/${encodeURIComponent(jobId)}`, 90000);
        setOutputHtml("create-output", renderCreateProgress(data.logs || []));

        if (data.status === "completed") {
          stopCreatePolling();
          state.activeCreateJobId = null;
          setStatus("create-status", `Script creation complete for "${data.topic}".`);
          setOutputHtml("create-output", renderScriptResult(data.result, true));
          return;
        }

        if (data.status === "failed") {
          stopCreatePolling();
          state.activeCreateJobId = null;
          setStatus("create-status", data.error || "Script creation failed.");
          setOutputHtml("create-output", renderCreateProgress(data.logs || []));
        }
      } catch (error) {
        stopCreatePolling();
        state.activeCreateJobId = null;
        setStatus("create-status", error.message || "Create polling failed.");
      }
    }

    function formatTimestamp(isoStr) {
      if (!isoStr) return "";
      // "2026-04-06T14:32:05.123456" → "2026-04-06 14:32"
      return isoStr.replace("T", " ").slice(0, 16);
    }

    function populateSelect(selectId, jobs) {
      const sel = document.getElementById(selectId);
      if (!sel || !jobs || !jobs.length) return;
      while (sel.options.length > 1) sel.remove(1);
      jobs.forEach((j) => {
        const opt = document.createElement("option");
        opt.value = j.job_id;
        opt.textContent = `${j.query} — ${formatNumber(j.result_count || 0)} results  (${formatTimestamp(j.created_at)})`;
        sel.appendChild(opt);
      });
    }

    async function loadPastOutlierJob(jobId) {
      try {
        const data = await getJson(`/api/v1/past-outliers/${encodeURIComponent(jobId)}`);
        state.latestOutliers = (data.videos || []).map((v) => ({
          title: v.title,
          url: v.url,
          views: v.views,
          median_views: v.median_views,
          ratio: v.ratio,
          channel: v.channel,
          subscribers: v.subscribers,
          success_criteria: v.success_criteria,
          subtopics_covered: v.subtopics_covered,
          reusable_insights: v.reusable_insights,
          ultimate_titles: v.ultimate_titles,
          alternate_hooks: v.alternate_hooks,
        }));
        state.selectedUrls = new Set(state.latestOutliers.map((item) => item.url));
        setStatus("outlier-status", `Loaded ${state.latestOutliers.length} outliers from past run.`);
        setOutputHtml("outlier-output", renderOutlierCards(state.latestOutliers));
      } catch (error) {
        setStatus("outlier-status", error.message || "Failed to load past outlier run.");
      }
    }

    function renderPastThemeDropdown(themes) {
      if (!themes || !themes.length) {
        return "";
      }
      return `
        <div class="field">
          <span class="field-label">Load Past Theme</span>
          <select id="past-theme-select">
            <option value="">— Select a past theme —</option>
            ${themes.map((t) => `<option value="${t.id}">${escapeHtml(t.topic)} (${t.created_at.split("T")[0]})</option>`).join("")}
          </select>
        </div>
      `;
    }

    async function loadPastTheme(themeId) {
      try {
        const data = await getJson(`/api/v1/past-themes/${themeId}`);
        state.latestTheme = { topic: data.topic, themes: data.themes_data };
        syncTopicFields(data.topic);
        setStatus("theme-status", `Loaded saved theme for "${data.topic}".`);
        setOutputHtml("theme-output", renderTheme({ topic: data.topic, themes: data.themes_data }));
      } catch (error) {
        setStatus("theme-status", error.message || "Failed to load past theme.");
      }
    }

    async function loadPastResearch(researchId) {
      try {
        const data = await getJson(`/api/v1/past-research/${encodeURIComponent(researchId)}`);
        const rd = data.research_data || {};
        state.latestResearch = rd;
        state.selectedResearchTitle = "";
        state.selectedResearchTopics = new Set();
        state.selectedThumbnail = null;
        if (data.topic) syncTopicFields(data.topic);
        setStatus("research-status", `Loaded saved research for "${data.topic}" (${data.created_at.split("T")[0]}). Select a title and topics.`);
        setOutputHtml("research-output", renderResearch(rd));
        updateHtpResearchSummary();
      } catch (error) {
        setStatus("research-status", error.message || "Failed to load past research.");
      }
    }

    function _htpLabel(r) {
      const date = (r.created_at || "").split("T")[0];
      const title = r.title ? ` — "${r.title}"` : "";
      return `${r.topic}${title} (${date})`;
    }

    async function loadPastHooksTp(htpId) {
      try {
        const data = await getJson(`/api/v1/past-hooks-tp/${encodeURIComponent(htpId)}`);
        const htp = data.htp_data || {};
        state.latestHooksTalkingPoints = htp;
        state.htpTitle = data.title || "";
        state.selectedHookScript = htp.hooks?.[0]?.thirty_sec_script || "";
        state.editedTalkingPoints = htp.talking_points || {sections: []};
        state.editedOutro = htp.outro || "";
        setStatus("create-status", `Loaded hooks & talking points for "${data.topic}" — "${data.title}".`);
        setOutputHtml("htp-output", renderHooksTalkingPoints(htp));
      } catch (error) {
        setStatus("create-status", error.message || "Failed to load past hooks & talking points.");
      }
    }

    async function loadPastRuns() {
      try {
        const [outlierData, discoveryData, themeData, researchData, htpData] = await Promise.all([
          getJson("/api/v1/past-outliers"),
          getJson("/api/v1/past-discovery"),
          getJson("/api/v1/past-themes"),
          getJson("/api/v1/past-research"),
          getJson("/api/v1/past-hooks-tp"),
        ]);
        state.pastOutlierJobs = outlierData.jobs || [];
        state.pastDiscoveryJobs = discoveryData.jobs || [];
        state.pastThemes = themeData.themes || [];
        state.pastResearch = researchData.results || [];
        state.pastHooksTp = htpData.results || [];

        populateSelect("outlier-past-select", state.pastOutlierJobs);
        populateSelect("research-outlier-select", [
          ...state.pastOutlierJobs,
          ...state.pastDiscoveryJobs,
        ]);
        populateSelect("discovery-past-select", state.pastDiscoveryJobs);

        const researchOptions = state.pastResearch.map(r => ({
          job_id: r.id,
          query: `${r.topic} (${r.created_at.split("T")[0]})`,
        }));
        populateSelect("htp-past-research-select", researchOptions);

        const htpOptions = state.pastHooksTp.map(r => ({
          job_id: r.id,
          query: _htpLabel(r),
        }));
        populateSelect("create-htp-select", htpOptions);

        const themeHtml = renderPastThemeDropdown(state.pastThemes);
        if (themeHtml) setOutputHtml("theme-past-run", themeHtml);
      } catch (error) {
        // Silently fail — past runs are optional
      }
    }

    function renderTheme(result) {
      if (!result || result.error) {
        return `<p class="meta">${escapeHtml(result?.error || "Theme analysis failed.")}</p>`;
      }
      const themes = result.themes || {};
      const opportunities = themes.ranked_video_opportunities || [];
      return `
        <div class="cards">
          <div class="card">
            <span class="tag">${escapeHtml(result.topic || "Theme")}</span>
            <ul class="summary-list">
              <li><strong>Audience intent:</strong> ${escapeHtml(themes.audience_intent || "N/A")}</li>
              <li><strong>Common title phrases:</strong> ${escapeHtml((themes.common_title_phrases || []).join(", ") || "N/A")}</li>
              <li><strong>Recurring topics:</strong> ${escapeHtml((themes.recurring_topics || []).join(", ") || "N/A")}</li>
              <li><strong>Success patterns:</strong> ${escapeHtml((themes.success_criteria_patterns || []).join(", ") || "N/A")}</li>
            </ul>
          </div>
          <div class="card">
            <h3 class="title">Market Map</h3>
            <ul class="summary-list">
              <li><strong>Saturated angles:</strong> ${escapeHtml((themes.saturated_angles || []).join(", ") || "N/A")}</li>
              <li><strong>Open gaps:</strong> ${escapeHtml((themes.open_gaps || []).join(", ") || "N/A")}</li>
              <li><strong>Viewer desires:</strong> ${escapeHtml((themes.viewer_desires || []).join(", ") || "N/A")}</li>
            </ul>
          </div>
          ${opportunities.length ? `
            <div class="card">
              <h3 class="title">Ranked Video Opportunities</h3>
              <div class="cards">
                ${opportunities.map((item) => `
                  <div class="card">
                    <span class="tag">${escapeHtml(String(item.opportunity_score || 0))}/10 opportunity</span>
                    <h3 class="title">${escapeHtml(item.angle_name || "Video opportunity")}</h3>
                    <p class="meta"><strong>Viewer desire:</strong> ${escapeHtml(item.viewer_desire || "N/A")}</p>
                    <p class="meta"><strong>Why it is open:</strong> ${escapeHtml(item.why_it_is_open || "N/A")}</p>
                    <p class="meta"><strong>Recommended format:</strong> ${escapeHtml(item.recommended_format || "N/A")}</p>
                  </div>
                `).join("")}
              </div>
            </div>
          ` : ""}
        </div>
      `;
    }

    function renderResearch(result) {
      if (!result || result.error) {
        return `<p class="meta">${escapeHtml(result?.error || "Research analysis failed.")}</p>`;
      }

      const titles = result.best_titles || [];
      const topics = result.high_level_topics || [];
      const transcriptSources = result.transcript_sources || [];
      const discussionSources = result.discussion_sources || [];
      const summary = result.research_summary || {};
      const theme = result.theme_data || {};
      const opportunities = theme.ranked_video_opportunities || [];

      return `
        <div class="cards">
          <div class="card">
            <h3 class="title">Title Options</h3>
            <p class="meta" style="margin-bottom:12px">Select a title, then pick a thumbnail concept below it.</p>
            <div class="checkboxes">
              ${titles.length ? titles.map((item, ti) => {
                const thumbs = Array.isArray(item.thumbnails) ? item.thumbnails : [];
                const titleVal = item.title || "";
                const isTitleSelected = state.selectedResearchTitle === titleVal;
                return `
                <div class="title-option-block" style="margin-bottom:16px;padding:12px;border-radius:8px;border:1px solid rgba(158,178,198,${isTitleSelected ? "0.35" : "0.12"});background:rgba(22,33,45,${isTitleSelected ? "0.8" : "0.4"});transition:all 0.2s">
                  <label class="checkbox-row" style="margin-bottom:${thumbs.length ? "10px" : "0"}">
                    <input type="radio" name="research-title" value="${escapeHtml(titleVal)}" ${isTitleSelected ? "checked" : ""}>
                    <h3 class="title" style="margin:0">${escapeHtml(titleVal || "Title option")}</h3>
                  </label>
                  ${thumbs.length ? `
                  <div class="thumbnail-options" style="margin-left:24px;display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start">
                    ${thumbs.map((th, thi) => {
                      const thumbKey = `${ti}-${thi}`;
                      const isSelected = state.selectedThumbnail && state.selectedThumbnail._key === thumbKey;
                      return `
                      <label style="cursor:pointer;width:calc(50% - 5px);box-sizing:border-box;padding:10px;border-radius:6px;border:1px solid rgba(99,179,237,${isSelected ? "0.5" : "0.2"});background:rgba(99,179,237,${isSelected ? "0.1" : "0.04"});transition:all 0.2s">
                        <div style="display:flex;align-items:flex-start;gap:8px;text-align:left">
                          <input type="radio" name="thumbnail-select" data-title-idx="${ti}" data-thumb-idx="${thi}" style="margin-top:3px;flex-shrink:0" ${isSelected ? "checked" : ""}>
                          <div>
                            <div style="font-size:0.8rem;font-weight:700;color:#63b3ed;letter-spacing:0.05em;margin-bottom:4px">${escapeHtml(th.text_overlay || "")}</div>
                            <div style="font-size:0.78rem;color:#a0aec0;margin-bottom:4px">${escapeHtml(th.visual_concept || "")}</div>
                            <div style="font-size:0.75rem;color:#718096"><span style="opacity:0.7">Mood:</span> ${escapeHtml(th.color_scheme || "")} &nbsp;·&nbsp; <span style="opacity:0.7">Emotion:</span> ${escapeHtml(th.emotion_target || "")}</div>
                          </div>
                        </div>
                      </label>`;
                    }).join("")}
                  </div>` : ""}
                </div>`;
              }).join("") : '<p class="meta">No title options returned.</p>'}
            </div>
          </div>
          <div class="card">
            <h3 class="title">Topic Options</h3>
            <div class="checkboxes">
              ${topics.length ? topics.map((item) => {
                const count = item.video_count || 0;
                const badge = count >= 2 ? `<span class="badge badge-multi">${count} videos</span>` : "";
                const subs = Array.isArray(item.subtopics) && item.subtopics.length
                  ? `<ul class="subtopic-list">${item.subtopics.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>`
                  : "";
                return `
                <label class="checkbox-row">
                  <input type="checkbox" data-research-topic="${escapeHtml(item.topic || "")}" ${state.selectedResearchTopics.has(item.topic || "") ? "checked" : ""}>
                  <div>
                    <h3 class="title">${escapeHtml(item.topic || "Topic option")} ${badge}</h3>
                    ${subs}
                  </div>
                </label>`;
              }).join("") : '<p class="meta">No topic options returned.</p>'}
            </div>
          </div>
          <div class="card">
            <h3 class="title">Research Summary</h3>
            <ul class="summary-list">
              <li><strong>Main discussion:</strong> ${escapeHtml(summary.main_discussion || "N/A")}</li>
              <li><strong>Strongest evidence:</strong> ${escapeHtml((summary.strongest_evidence || []).join(", ") || "N/A")}</li>
              <li><strong>Recommended story spine:</strong> ${escapeHtml(summary.recommended_story_spine || "N/A")}</li>
            </ul>
          </div>
          ${Object.keys(theme).length ? `
            <div class="card">
              <h3 class="title">Market Map</h3>
              <ul class="summary-list">
                ${theme.audience_intent ? `<li><strong>Audience intent:</strong> ${escapeHtml(theme.audience_intent)}</li>` : ""}
                ${(theme.common_title_phrases || []).length ? `<li><strong>Common title phrases:</strong> ${escapeHtml(theme.common_title_phrases.join(", "))}</li>` : ""}
                ${(theme.recurring_topics || []).length ? `<li><strong>Recurring topics:</strong> ${escapeHtml(theme.recurring_topics.join(", "))}</li>` : ""}
                ${(theme.success_criteria_patterns || []).length ? `<li><strong>Success patterns:</strong> ${escapeHtml(theme.success_criteria_patterns.join(", "))}</li>` : ""}
              </ul>
            </div>
            <div class="card">
              <h3 class="title">Gaps &amp; Angles</h3>
              <ul class="summary-list">
                ${(theme.saturated_angles || []).length ? `<li><strong>Saturated angles</strong> (already covered — include if outliers used them): ${escapeHtml(theme.saturated_angles.join(", "))}</li>` : ""}
                ${(theme.open_gaps || []).length ? `<li><strong>Open gaps</strong> (underserved): ${escapeHtml(theme.open_gaps.join(", "))}</li>` : ""}
                ${(theme.viewer_desires || []).length ? `<li><strong>Viewer desires:</strong> ${escapeHtml(theme.viewer_desires.join(", "))}</li>` : ""}
              </ul>
            </div>
            ${opportunities.length ? `
              <div class="card">
                <h3 class="title">Ranked Video Opportunities</h3>
                <div class="cards">
                  ${opportunities.map((item) => `
                    <div class="card">
                      <span class="tag">${escapeHtml(String(item.opportunity_score || 0))}/10 opportunity</span>
                      <h3 class="title">${escapeHtml(item.angle_name || "Video opportunity")}</h3>
                      <p class="meta"><strong>Viewer desire:</strong> ${escapeHtml(item.viewer_desire || "N/A")}</p>
                      <p class="meta"><strong>Why it is open:</strong> ${escapeHtml(item.why_it_is_open || "N/A")}</p>
                      <p class="meta"><strong>Recommended format:</strong> ${escapeHtml(item.recommended_format || "N/A")}</p>
                    </div>
                  `).join("")}
                </div>
              </div>
            ` : ""}
          ` : ""}
          ${(() => {
            const redditItems = discussionSources.filter(d => d.source === "Reddit").slice(0, 3);
            const xItems = discussionSources.filter(d => d.source === "X").slice(0, 3);
            const filtered = [...redditItems, ...xItems];
            return filtered.length ? `
            <div class="card">
              <h3 class="title">Recent Discussions</h3>
              <div class="cards">
                ${filtered.map((item) => `
                  <div class="card">
                    <span class="tag">${escapeHtml(item.source || "Discussion")}</span>
                    <h3 class="title"><a class="link" href="${escapeHtml(item.url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(item.title || "Discussion source")}</a></h3>
                    <p class="meta">${escapeHtml(item.snippet || "No snippet available.")}</p>
                  </div>
                `).join("")}
              </div>
            </div>
          ` : "";
          })()}
          ${(() => {
            const available = transcriptSources.filter(s => s.transcript_excerpt);
            const unavailableCount = transcriptSources.length - available.length;
            if (!transcriptSources.length) return "";
            const links = available.map(s => `<a class="link" href="${escapeHtml(s.url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(s.title || s.url || "video")}</a>`).join(", ");
            const unavailableMsg = unavailableCount > 0 ? `<span class="meta"> — transcript unavailable for ${unavailableCount} video${unavailableCount > 1 ? "s" : ""}</span>` : "";
            return `
            <div class="card">
              <p class="meta"><strong>Transcripts:</strong> ${links || "None available"}${unavailableMsg}</p>
            </div>
          `;
          })()}
        </div>
      `;
    }

    function renderHooksTalkingPoints(data) {
      if (!data || data.error) {
        return `<p class="meta">${escapeHtml(data?.error || "Generation failed.")}</p>`;
      }
      const hooks = data.hooks || [];
      const sections = (data.talking_points || {}).sections || [];
      const outro = data.outro || "";
      const shorts = data.shorts_segments || [];

      const tpJson = JSON.stringify(data.talking_points || {sections: []}, null, 2);
      state.editedTalkingPoints = data.talking_points || {sections: []};
      state.editedOutro = outro;

      return `
        <div class="cards">
          <div class="card">
            <h3 class="title">Choose a Hook</h3>
            <p class="meta" style="margin-bottom:12px">Each includes the first 30 seconds of script. Select one — you can edit it below.</p>
            <div class="checkboxes" id="hook-list">
              ${hooks.map((h, i) => `
                <label class="checkbox-row">
                  <input type="radio" name="htp-hook" value="${i}" ${i === 0 ? "checked" : ""}>
                  <div style="width:100%">
                    <h3 class="title">${escapeHtml(h.hook_line || "Hook " + (i+1))}</h3>
                    <textarea class="hook-script-editor" data-hook-index="${i}" rows="4" style="width:100%;margin-top:6px;font-size:0.85rem">${escapeHtml(h.thirty_sec_script || "")}</textarea>
                  </div>
                </label>
              `).join("")}
            </div>
          </div>

          <div class="card">
            <h3 class="title">Talking Points Outline</h3>
            <p class="meta" style="margin-bottom:12px">Check/uncheck sections to include or exclude. Edit titles and bullets inline. Reorder with ↑↓. Add or remove sections, subsections, and bullets.</p>
            <div id="htp-tp-editor">
              ${renderTalkingPointsEditor(data.talking_points)}
            </div>
          </div>

          <div class="card">
            <h3 class="title">Outro <span class="meta" style="font-size:0.8rem;font-weight:400">— edit freely</span></h3>
            <textarea id="htp-outro-editor" rows="4" style="width:100%">${escapeHtml(outro)}</textarea>
          </div>

          ${shorts.length ? `
          <div class="card">
            <h3 class="title">Shorts Segments (${shorts.length})</h3>
            <p class="meta" style="margin-bottom:8px">These will be marked [SHORT START/END] in the script so you can cut them.</p>
            ${shorts.map(s => `
              <div style="margin-bottom:12px;padding:10px;border-radius:8px;background:rgba(99,179,237,0.06);border:1px solid rgba(99,179,237,0.15)">
                <strong style="font-size:0.9rem">${escapeHtml(s.title || "Short")}</strong>
                <span class="meta" style="margin-left:8px">from: ${escapeHtml(s.source_section || "")}</span>
                <p class="meta" style="margin-top:4px;font-style:italic">"${escapeHtml(s.hook_line || "")}"</p>
                <p class="meta" style="margin-top:4px;white-space:pre-wrap">${escapeHtml(s.script || "")}</p>
              </div>
            `).join("")}
          </div>` : ""}
        </div>
      `;
    }

    function renderTalkingPointsEditor(tp) {
      const sections = (tp && tp.sections) ? tp.sections : [];
      if (!sections.length) {
        return `<p class="meta" style="margin-bottom:8px">No sections yet.</p>
          <button class="btn-add tp-add-section">+ Add Section</button>`;
      }
      return `
        ${sections.map((sec, si) => {
          const excluded = sec._excluded || false;
          const borderColor = excluded ? "rgba(245,101,101,0.25)" : "rgba(99,179,237,0.2)";
          const bg = excluded ? "rgba(245,101,101,0.04)" : "rgba(22,33,45,0.5)";
          return `
          <div class="tp-section-block" style="margin-bottom:10px;border:1px solid ${borderColor};border-radius:8px;padding:10px 12px;background:${bg};opacity:${excluded ? 0.6 : 1}">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
              <input type="checkbox" class="tp-sec-toggle" data-si="${si}" ${excluded ? "" : "checked"} title="Include in script" style="width:auto;margin:0;cursor:pointer;flex-shrink:0">
              <input type="text" class="tp-sec-title" data-si="${si}" value="${escapeHtml(sec.title || "")}" placeholder="Section title" style="flex:1;font-size:0.92rem;font-weight:600">
              <div style="display:flex;gap:3px;flex-shrink:0">
                ${si > 0 ? `<button class="btn-icon tp-sec-up" data-si="${si}" title="Move up">↑</button>` : ""}
                ${si < sections.length - 1 ? `<button class="btn-icon tp-sec-dn" data-si="${si}" title="Move down">↓</button>` : ""}
                <button class="btn-icon btn-danger tp-sec-del" data-si="${si}" title="Remove section">✕</button>
              </div>
            </div>
            <div style="margin-left:22px">
              ${(sec.subsections || []).map((sub, subi) => `
                <div style="margin-bottom:8px;padding:7px 10px;border-radius:6px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06)">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
                    <input type="text" class="tp-sub-title" data-si="${si}" data-subi="${subi}" value="${escapeHtml(sub.title || "")}" placeholder="Subsection title" style="flex:1;font-size:0.85rem;color:rgba(210,225,240,0.85)">
                    <div style="display:flex;gap:3px;flex-shrink:0">
                      ${subi > 0 ? `<button class="btn-icon tp-sub-up" data-si="${si}" data-subi="${subi}" title="Move up">↑</button>` : ""}
                      ${subi < (sec.subsections || []).length - 1 ? `<button class="btn-icon tp-sub-dn" data-si="${si}" data-subi="${subi}" title="Move down">↓</button>` : ""}
                      <button class="btn-icon btn-danger tp-sub-del" data-si="${si}" data-subi="${subi}" title="Remove subsection">✕</button>
                    </div>
                  </div>
                  <div style="margin-left:8px">
                    ${(sub.bullets || []).map((b, bi) => `
                      <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
                        <span style="color:#4a5568;flex-shrink:0">•</span>
                        <input type="text" class="tp-bullet-input" data-si="${si}" data-subi="${subi}" data-bi="${bi}" value="${escapeHtml(b || "")}" placeholder="Talking point..." style="flex:1;font-size:0.82rem;color:#a0aec0">
                        <button class="btn-icon btn-danger tp-bul-del" data-si="${si}" data-subi="${subi}" data-bi="${bi}" title="Remove bullet" style="padding:2px 5px">✕</button>
                      </div>
                    `).join("")}
                    <button class="btn-add tp-add-bullet" data-si="${si}" data-subi="${subi}" style="margin-top:4px;font-size:0.75rem">+ bullet</button>
                  </div>
                </div>
              `).join("")}
              <button class="btn-add tp-add-sub" data-si="${si}" style="margin-top:2px;font-size:0.78rem">+ subsection</button>
            </div>
          </div>`;
        }).join("")}
        <button class="btn-add tp-add-section" style="margin-top:6px">+ Add Section</button>
      `;
    }

    function renderScriptResult(result, includeQuality = true) {
      if (!result) {
        return '<p class="meta">No result returned.</p>';
      }
      const qualityScore = result.quality_report?.overall_score;
      return `
        <div class="cards">
          <div class="card">
            <span class="tag">${includeQuality && qualityScore !== undefined ? `${qualityScore}/100 quality` : "Generated"}</span>
            <h3 class="title">${escapeHtml(result.topic || "Script")}</h3>
            <p class="meta">Duration: ${escapeHtml(String(result.duration || "N/A"))} min</p>
            <div class="line">Selected angles: ${escapeHtml((result.selected_angles || []).map((a) => a.angle_name).join(", ") || "Auto")}</div>
          </div>
          <div class="card">
            <h3 class="title">Script</h3>
            <div class="mono">${escapeHtml(result.script || "")}</div>
          </div>
        </div>
      `;
    }

    document.getElementById("outlier-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const query = document.getElementById("outlier-topic").value.trim();
      const limit = Number(document.getElementById("outlier-limit").value || 10);
      const maxSubscribers = Number(document.getElementById("outlier-max-subscribers").value || 0);
      const includeInsights = document.getElementById("outlier-insights").checked;
      syncTopicFields(query);
      stopOutlierPolling();
      setStatus("outlier-status", `Running outlier search for "${query}"...`);
      setOutputHtml("outlier-output", renderOutlierProgress([`[*] Queuing outlier search for "${query}"...`]));

      try {
        const job = await postJson("/api/v1/app/outlier/start", {
          query,
          limit,
          include_insights: includeInsights,
          max_subscribers: maxSubscribers > 0 ? maxSubscribers : null
        });
        state.activeOutlierJobId = job.job_id;
        setStatus("outlier-status", `Outlier search started for "${job.query}". Showing live progress...`);
        await pollOutlierJob(job.job_id);
        if (state.activeOutlierJobId) {
          state.outlierPollTimer = setInterval(() => {
            pollOutlierJob(job.job_id);
          }, 2000);
        }
      } catch (error) {
        setStatus("outlier-status", error.message || "Outlier search failed.");
        setOutputHtml("outlier-output", `<p class="meta">${escapeHtml(error.message || "Outlier search failed.")}</p>`);
      }
    });

    document.getElementById("trend-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const seeds = document.getElementById("trend-seeds").value.trim();
      const lookbackDays = Number(document.getElementById("trend-lookback").value || 14);
      const maxVideosPerSeed = Number(document.getElementById("trend-limit").value || 15);
      const maxTerms = Number(document.getElementById("trend-max-terms").value || 12);
      const aiOnly = document.getElementById("trend-ai-only").checked;
      stopTrendPolling();
      setStatus("trend-status", "Running trend discovery...");
      setOutputHtml("trend-output", renderTrendProgress([`[*] Queuing trend discovery for ${lookbackDays} day lookback...`]));
      try {
        const job = await postJson("/api/v1/app/trends/start", {
          seeds,
          lookback_days: lookbackDays,
          max_videos_per_seed: maxVideosPerSeed,
          ai_only: aiOnly,
          max_terms: maxTerms
        });
        state.activeTrendJobId = job.job_id;
        setStatus("trend-status", "Trend discovery started. Showing live progress...");
        await pollTrendJob(job.job_id);
        if (state.activeTrendJobId) {
          state.trendPollTimer = setInterval(() => {
            pollTrendJob(job.job_id);
          }, 2000);
        }
      } catch (error) {
        setStatus("trend-status", error.message || "Trend discovery failed.");
        setOutputHtml("trend-output", `<p class="meta">${escapeHtml(error.message || "Trend discovery failed.")}</p>`);
      }
    });

    document.getElementById("outlier-output").addEventListener("change", (event) => {
      if (event.target.matches('input[type="checkbox"][data-url]')) {
        const url = event.target.getAttribute("data-url");
        if (event.target.checked) {
          state.selectedUrls.add(url);
        } else {
          state.selectedUrls.delete(url);
        }
        setStatus("outlier-status", `${state.selectedUrls.size} outliers selected for downstream workflows.`);
      }
    });

    document.getElementById("discovery-output").addEventListener("change", (event) => {
      if (event.target.matches('input[type="checkbox"][data-url]')) {
        const url = event.target.getAttribute("data-url");
        if (event.target.checked) {
          state.selectedUrls.add(url);
        } else {
          state.selectedUrls.delete(url);
        }
        setStatus("discovery-status", `${state.selectedUrls.size} videos selected for Titles &amp; Topics and Create.`);
      }
    });

    document.getElementById("discovery-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const terms = document.getElementById("discovery-terms").value.trim();
      stopDiscoveryPolling();
      setStatus("discovery-status", "Running discovery...");
      setOutputHtml("discovery-output", renderDiscoveryProgress([`[*] Queuing discovery for: ${terms}`]));
      try {
        const job = await postJson("/api/v1/app/discovery/start", { terms });
        state.activeDiscoveryJobId = job.job_id;
        setStatus("discovery-status", "Discovery started. Showing live progress...");
        await pollDiscoveryJob(job.job_id);
        if (state.activeDiscoveryJobId) {
          state.discoveryPollTimer = setInterval(() => {
            pollDiscoveryJob(job.job_id);
          }, 2000);
        }
      } catch (error) {
        setStatus("discovery-status", error.message || "Discovery failed.");
        setOutputHtml("discovery-output", `<p class="meta">${escapeHtml(error.message || "Discovery failed.")}</p>`);
      }
    });

    document.getElementById("theme-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const topic = document.getElementById("theme-topic").value.trim();
      const chosen = selectedOutliers();
      const videos = chosen.length ? chosen : state.latestOutliers;
      setStatus("theme-status", `Analyzing themes for "${topic}"...`);
      setOutputHtml("theme-output", '<p class="meta">Extracting themes...</p>');
      try {
        const data = await postJson("/api/v1/app/theme", { topic, videos: videos.length ? videos : null });
        state.latestTheme = data;
        setStatus("theme-status", `Theme analysis complete for "${topic}".`);
        setOutputHtml("theme-output", renderTheme(data));
      } catch (error) {
        setStatus("theme-status", error.message || "Theme failed.");
        setOutputHtml("theme-output", `<p class="meta">${escapeHtml(error.message || "Theme failed.")}</p>`);
      }
    });

    document.getElementById("research-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const outlierJobId = document.getElementById("research-outlier-select").value;
      const sources = document.getElementById("research-sources").value.trim();
      const notes = document.getElementById("research-notes").value.trim();

      let videos = [];
      let topic = "";

      if (outlierJobId && outlierJobId !== "current") {
        setStatus("research-status", "Loading selected outlier set...");
        setOutputHtml("research-output", '<p class="meta">Fetching outlier videos...</p>');
        try {
          const data = await getJson(`/api/v1/past-outliers/${encodeURIComponent(outlierJobId)}`);
          videos = (data.videos || []).map((v) => ({
            title: v.title, url: v.url, views: v.views,
            median_views: v.median_views, ratio: v.ratio,
            channel: v.channel, subscribers: v.subscribers,
            success_criteria: v.success_criteria,
            subtopics_covered: v.subtopics_covered,
            reusable_insights: v.reusable_insights,
            ultimate_titles: v.ultimate_titles,
            alternate_hooks: v.alternate_hooks,
          }));
          const job = state.pastOutlierJobs.find((j) => j.job_id === outlierJobId);
          topic = job?.query || "";
        } catch (e) {
          setStatus("research-status", "Failed to load selected outlier set.");
          setOutputHtml("research-output", `<p class="meta">${escapeHtml(e.message || "Load failed.")}</p>`);
          return;
        }
      } else {
        const chosen = selectedOutliers();
        videos = chosen.length ? chosen : state.latestOutliers;
        topic = document.getElementById("outlier-topic")?.value?.trim() || "video";
      }

      if (!videos.length) {
        setStatus("research-status", "No outlier videos available. Run an Outlier search first or select a past run above.");
        setOutputHtml("research-output", '<p class="meta">Select an outlier set to get started.</p>');
        return;
      }

      syncTopicFields(topic);
      setStatus("research-status", `Getting titles and topics for "${topic}"...`);
      setOutputHtml("research-output", '<p class="meta">Analyzing outlier videos for best titles and topics...</p>');
      try {
        const data = await postJson("/api/v1/app/research", {
          topic,
          custom_links: sources,
          custom_notes: notes,
          theme_data: state.latestTheme?.themes || null,
          videos
        }, 600000);
        state.latestResearch = data;
        state.selectedResearchTitle = "";
        state.selectedResearchTopics = new Set();
        state.selectedThumbnail = null;
        // Store theme data for downstream use in Create Script
        if (data.theme_data && Object.keys(data.theme_data).length) {
          state.latestTheme = { topic, themes: data.theme_data };
          syncTopicFields(topic);
        }
        setStatus("research-status", `Titles and topics ready for "${topic}". Select one title and at least one topic.`);
        setOutputHtml("research-output", renderResearch(data));
      } catch (error) {
        setStatus("research-status", error.message || "Research failed.");
        setOutputHtml("research-output", `<p class="meta">${escapeHtml(error.message || "Research failed.")}</p>`);
      }
    });

    function updateHtpResearchSummary() {
      const el = document.getElementById("htp-research-summary");
      if (!el) return;
      const title = state.selectedResearchTitle;
      const topics = Array.from(state.selectedResearchTopics);
      if (!title && !topics.length) {
        el.style.display = "none";
        return;
      }
      el.style.display = "block";
      const topicList = topics.length
        ? topics.map(t => `<span style="display:inline-block;background:rgba(99,179,237,0.12);border:1px solid rgba(99,179,237,0.25);border-radius:12px;padding:2px 9px;margin:2px 3px 2px 0;font-size:0.8rem">${escapeHtml(t)}</span>`).join("")
        : '<span style="opacity:0.5">None selected</span>';
      el.innerHTML = `<strong style="display:block;margin-bottom:6px;font-size:0.85rem">Selected for hook generation:</strong>`
        + (title ? `<div style="margin-bottom:6px"><strong>Title:</strong> ${escapeHtml(title)}</div>` : "")
        + `<div><strong>Topics:</strong> ${topicList}</div>`;
    }

    document.getElementById("research-output").addEventListener("change", (event) => {
      if (event.target.matches('input[type="radio"][name="research-title"]')) {
        state.selectedResearchTitle = event.target.value;
        // Reset thumbnail selection when title changes
        state.selectedThumbnail = null;
        setStatus("research-status", `Selected title: ${state.selectedResearchTitle}`);
        // Re-render to update border highlights on title blocks
        if (state.latestResearch) setOutputHtml("research-output", renderResearch(state.latestResearch));
      }
      if (event.target.matches('input[type="radio"][name="thumbnail-select"]')) {
        const ti = parseInt(event.target.getAttribute("data-title-idx"), 10);
        const thi = parseInt(event.target.getAttribute("data-thumb-idx"), 10);
        const titles = (state.latestResearch || {}).best_titles || [];
        const titleObj = titles[ti] || {};
        const thumbs = titleObj.thumbnails || [];
        const thumb = thumbs[thi];
        if (thumb) {
          state.selectedThumbnail = { ...thumb, _key: `${ti}-${thi}` };
          setStatus("research-status", `Thumbnail selected: "${thumb.text_overlay || "Option " + (thi + 1)}"`);
        }
      }
      if (event.target.matches('input[type="checkbox"][data-research-topic]')) {
        const topic = event.target.getAttribute("data-research-topic");
        if (event.target.checked) {
          state.selectedResearchTopics.add(topic);
        } else {
          state.selectedResearchTopics.delete(topic);
        }
        setStatus("research-status", `${state.selectedResearchTopics.size} research topic(s) selected.`);
      }
      updateHtpResearchSummary();
    });

    // HTP form: generate hooks & talking points
    document.getElementById("htp-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const customTitle = document.getElementById("htp-custom-title").value.trim();
      const customNotes = document.getElementById("htp-custom-notes").value.trim();
      const title = customTitle || state.selectedResearchTitle;
      const topics = Array.from(state.selectedResearchTopics);
      const topic = title || state.selectedResearchTitle || "AI agents";

      if (!title && !topics.length) {
        setStatus("htp-status", "Run Titles & Topics first and select a title and topics.");
        return;
      }
      setStatus("htp-status", "Generating hooks and talking points...");
      setOutputHtml("htp-output", '<p class="meta">Building hook options and talking points outline...</p>');
      try {
        const data = await postJson("/api/v1/app/hooks-talking-points", {
          topic,
          title,
          topics,
          custom_notes: customNotes,
        }, 120000);
        state.latestHooksTalkingPoints = data;
        state.htpTitle = title;
        state.selectedHookScript = (data.hooks && data.hooks[0]) ? data.hooks[0].thirty_sec_script : "";
        state.editedTalkingPoints = data.talking_points || {sections: []};
        state.editedOutro = data.outro || "";
        setStatus("htp-status", "Hooks and talking points ready. Select a hook, edit the outline, then Create Script.");
        setOutputHtml("htp-output", renderHooksTalkingPoints(data));
      } catch (error) {
        setStatus("htp-status", error.message || "Generation failed.");
        setOutputHtml("htp-output", `<p class="meta">${escapeHtml(error.message || "Generation failed.")}</p>`);
      }
    });

    // Helper: re-render just the talking points editor in-place
    function refreshTpEditor() {
      const el = document.getElementById("htp-tp-editor");
      if (el) el.innerHTML = renderTalkingPointsEditor(state.editedTalkingPoints);
    }

    // Sync hook selection and live edits from HTP output
    document.getElementById("htp-output").addEventListener("change", (event) => {
      if (event.target.matches('input[type="radio"][name="htp-hook"]')) {
        const idx = parseInt(event.target.value, 10);
        const ta = document.querySelector(`.hook-script-editor[data-hook-index="${idx}"]`);
        if (ta) state.selectedHookScript = ta.value;
      }
      // Section include/exclude toggle
      if (event.target.matches(".tp-sec-toggle")) {
        const si = parseInt(event.target.dataset.si);
        state.editedTalkingPoints.sections[si]._excluded = !event.target.checked;
        refreshTpEditor();
      }
    });

    document.getElementById("htp-output").addEventListener("input", (event) => {
      if (event.target.matches(".hook-script-editor")) {
        const selected = document.querySelector('input[name="htp-hook"]:checked');
        if (selected && parseInt(selected.value, 10) === parseInt(event.target.dataset.hookIndex, 10)) {
          state.selectedHookScript = event.target.value;
        }
      }
      if (event.target.id === "htp-outro-editor") {
        state.editedOutro = event.target.value;
      }
      // Inline text edits — update state without re-rendering (preserve focus)
      if (event.target.matches(".tp-sec-title")) {
        const si = parseInt(event.target.dataset.si);
        state.editedTalkingPoints.sections[si].title = event.target.value;
      }
      if (event.target.matches(".tp-sub-title")) {
        const si = parseInt(event.target.dataset.si), subi = parseInt(event.target.dataset.subi);
        state.editedTalkingPoints.sections[si].subsections[subi].title = event.target.value;
      }
      if (event.target.matches(".tp-bullet-input")) {
        const si = parseInt(event.target.dataset.si), subi = parseInt(event.target.dataset.subi), bi = parseInt(event.target.dataset.bi);
        state.editedTalkingPoints.sections[si].subsections[subi].bullets[bi] = event.target.value;
      }
    });

    document.getElementById("htp-output").addEventListener("click", (event) => {
      const btn = event.target.closest("button");
      if (!btn) return;
      const tp = state.editedTalkingPoints;
      const secs = tp.sections;

      if (btn.matches(".tp-sec-up")) {
        const si = parseInt(btn.dataset.si);
        if (si > 0) { [secs[si-1], secs[si]] = [secs[si], secs[si-1]]; refreshTpEditor(); }
      } else if (btn.matches(".tp-sec-dn")) {
        const si = parseInt(btn.dataset.si);
        if (si < secs.length-1) { [secs[si], secs[si+1]] = [secs[si+1], secs[si]]; refreshTpEditor(); }
      } else if (btn.matches(".tp-sec-del")) {
        const si = parseInt(btn.dataset.si);
        secs.splice(si, 1);
        refreshTpEditor();
      } else if (btn.matches(".tp-add-section")) {
        secs.push({ title: "New Section", subsections: [{ title: "Subsection", bullets: ["Talking point"] }] });
        refreshTpEditor();
      } else if (btn.matches(".tp-sub-up")) {
        const si = parseInt(btn.dataset.si), subi = parseInt(btn.dataset.subi);
        const subs = secs[si].subsections;
        if (subi > 0) { [subs[subi-1], subs[subi]] = [subs[subi], subs[subi-1]]; refreshTpEditor(); }
      } else if (btn.matches(".tp-sub-dn")) {
        const si = parseInt(btn.dataset.si), subi = parseInt(btn.dataset.subi);
        const subs = secs[si].subsections;
        if (subi < subs.length-1) { [subs[subi], subs[subi+1]] = [subs[subi+1], subs[subi]]; refreshTpEditor(); }
      } else if (btn.matches(".tp-sub-del")) {
        const si = parseInt(btn.dataset.si), subi = parseInt(btn.dataset.subi);
        secs[si].subsections.splice(subi, 1);
        refreshTpEditor();
      } else if (btn.matches(".tp-add-sub")) {
        const si = parseInt(btn.dataset.si);
        secs[si].subsections.push({ title: "New Subsection", bullets: ["Talking point"] });
        refreshTpEditor();
      } else if (btn.matches(".tp-bul-del")) {
        const si = parseInt(btn.dataset.si), subi = parseInt(btn.dataset.subi), bi = parseInt(btn.dataset.bi);
        secs[si].subsections[subi].bullets.splice(bi, 1);
        refreshTpEditor();
      } else if (btn.matches(".tp-add-bullet")) {
        const si = parseInt(btn.dataset.si), subi = parseInt(btn.dataset.subi);
        secs[si].subsections[subi].bullets.push("");
        refreshTpEditor();
      }
    });

    document.getElementById("create-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const notes = document.getElementById("create-notes").value;
      const duration = Number(document.getElementById("create-duration").value || 11);
      const topN = Number(document.getElementById("create-top-n").value || 10);
      const selectedVideos = selectedOutliers();

      // Load HTP from past-run dropdown if selected (overrides current session)
      const htpSelectVal = document.getElementById("create-htp-select").value;
      if (htpSelectVal) {
        await loadPastHooksTp(htpSelectVal);
      }

      // Require either full Research handoff OR a loaded HTP with talking points + hook
      const hasResearch = state.selectedResearchTitle && state.selectedResearchTopics.size && state.latestResearch;
      const hasHtp = state.editedTalkingPoints?.sections?.length && state.selectedHookScript;

      if (!hasResearch && !hasHtp) {
        setStatus("create-status", "Complete Hooks & Talking Points first (select a hook and have at least one talking-point section), or run Titles & Topics and select a title and topics.");
        setOutputHtml("create-output", '<p class="meta">Need either a complete Hooks & Talking Points selection or a Research handoff to generate the script.</p>');
        return;
      }

      // Resolve title and topics — prefer Research selection, fall back to HTP title + section titles
      const resolvedTitle = state.selectedResearchTitle || state.htpTitle || "";
      const resolvedTopics = state.selectedResearchTopics.size
        ? Array.from(state.selectedResearchTopics)
        : (state.editedTalkingPoints?.sections || []).filter(s => !s._excluded).map(s => s.title);
      const topic = resolvedTitle || "video";

      stopCreatePolling();
      setStatus("create-status", `Running full create workflow for "${topic}"...`);
      setOutputHtml("create-output", renderCreateProgress([`[*] Queuing script creation for "${topic}"...`]));

      // Capture outro edit
      const htpOutro = document.getElementById("htp-outro-editor");
      if (htpOutro) state.editedOutro = htpOutro.value;
      const selectedHookRadio = document.querySelector('input[name="htp-hook"]:checked');
      if (selectedHookRadio) {
        const idx = parseInt(selectedHookRadio.value, 10);
        const ta = document.querySelector(`.hook-script-editor[data-hook-index="${idx}"]`);
        if (ta) state.selectedHookScript = ta.value;
      }

      try {
        const job = await postJson("/api/v1/app/create/start", {
          topic,
          notes,
          duration,
          strategy: "outliers",
          top_n_outliers: topN,
          selected_videos: selectedVideos.length ? selectedVideos : null,
          selected_title: resolvedTitle,
          selected_topics: resolvedTopics,
          research_packet: state.latestResearch || null,
          selected_hook_script: state.selectedHookScript || null,
          talking_points: state.editedTalkingPoints ? {
            sections: (state.editedTalkingPoints.sections || []).filter(s => !s._excluded)
          } : null,
          outro: state.editedOutro || null,
          shorts_segments: state.latestHooksTalkingPoints?.shorts_segments || null,
          selected_thumbnail: state.selectedThumbnail || null,
        }, 30000);
        state.activeCreateJobId = job.job_id;
        setStatus("create-status", `Script creation started for "${job.topic}". Showing live progress...`);
        await pollCreateJob(job.job_id);
        if (state.activeCreateJobId) {
          state.createPollTimer = setInterval(() => {
            pollCreateJob(job.job_id);
          }, 2000);
        }
      } catch (error) {
        setStatus("create-status", error.message || "Create failed.");
        setOutputHtml("create-output", `<p class="meta">${escapeHtml(error.message || "Create failed.")}</p>`);
      }
    });

    document.getElementById("outlier-past-select").addEventListener("change", (event) => {
      if (event.target.value) loadPastOutlierJob(event.target.value);
    });

    document.getElementById("discovery-past-select").addEventListener("change", async (event) => {
      const jobId = event.target.value;
      if (!jobId) return;
      try {
        const data = await getJson(`/api/v1/past-discovery/${encodeURIComponent(jobId)}`);
        state.latestOutliers = (data.videos || []).map((v) => ({
          title: v.title, url: v.url, views: v.views,
          median_views: v.median_views, ratio: v.ratio,
          channel: v.channel, subscribers: v.subscribers,
          success_criteria: v.success_criteria,
          subtopics_covered: v.subtopics_covered,
          reusable_insights: v.reusable_insights,
          ultimate_titles: v.ultimate_titles,
          alternate_hooks: v.alternate_hooks,
        }));
        state.selectedUrls = new Set(state.latestOutliers.map((item) => item.url));
        const job = state.pastDiscoveryJobs.find((j) => j.job_id === jobId);
        if (job) syncTopicFields(job.query);
        setStatus("discovery-status", `Loaded ${state.latestOutliers.length} videos from discovery run "${job?.query || jobId}". Select rows to use downstream.`);
        setOutputHtml("discovery-output", renderDiscovery(state.latestOutliers, job?.query));
      } catch (error) {
        setStatus("discovery-status", error.message || "Failed to load past discovery run.");
      }
    });

    document.getElementById("theme-past-run").addEventListener("change", (event) => {
      if (event.target.id === "past-theme-select" && event.target.value) {
        loadPastTheme(event.target.value);
      }
    });

    document.getElementById("create-htp-select").addEventListener("change", (event) => {
      if (event.target.value) loadPastHooksTp(event.target.value);
    });

    document.getElementById("htp-past-research-select").addEventListener("change", async (event) => {
      const id = event.target.value;
      if (!id) return;
      try {
        const data = await getJson(`/api/v1/past-research/${encodeURIComponent(id)}`);
        const rd = data.research_data || {};
        // Load into session state so HTP form can use it
        state.latestResearch = rd;
        state.selectedResearchTitle = "";
        state.selectedResearchTopics = new Set();
        state.selectedThumbnail = null;
        if (data.topic) syncTopicFields(data.topic);
        setStatus("htp-status", `Loaded research for "${data.topic}". Select a title and topics below, then generate hooks.`);
        setOutputHtml("research-output", renderResearch(rd));
        updateHtpResearchSummary();
        // Scroll to research section so user can pick title/topics
        document.getElementById("research").scrollIntoView({ behavior: "smooth" });
      } catch (error) {
        setStatus("htp-status", error.message || "Failed to load past research.");
      }
    });

    document.getElementById("logout-button").addEventListener("click", logout);
    loadPastRuns();
  </script>
</body>
</html>
"""
