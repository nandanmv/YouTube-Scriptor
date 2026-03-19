def render_app_ui() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Strategy OS</title>
  <style>
    :root {
      --bg: #f4efe7;
      --surface: rgba(255, 252, 246, 0.92);
      --surface-2: rgba(255, 255, 255, 0.78);
      --ink: #1f2933;
      --muted: #5b6770;
      --accent: #d94841;
      --line: rgba(31, 41, 51, 0.12);
      --shadow: 0 18px 48px rgba(84, 67, 48, 0.16);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(217, 72, 65, 0.16), transparent 30%),
        radial-gradient(circle at left 20%, rgba(31, 41, 51, 0.08), transparent 28%),
        linear-gradient(180deg, #f8f4ed 0%, var(--bg) 100%);
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
      background: linear-gradient(135deg, var(--accent), #b8322b);
      box-shadow: 0 8px 18px rgba(217, 72, 65, 0.18);
    }

    .button-link.secondary {
      color: var(--ink);
      background: rgba(255,255,255,0.84);
      border: 1px solid var(--line);
      box-shadow: none;
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
      background: rgba(255,255,255,0.72);
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
      background: rgba(255,255,255,0.82);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
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
      background: linear-gradient(135deg, var(--accent), #b8322b);
      box-shadow: 0 8px 18px rgba(217, 72, 65, 0.18);
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
      border: 1px solid rgba(31, 41, 51, 0.08);
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
      background: rgba(244, 239, 231, 0.82);
    }

    .tag {
      display: inline-flex;
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(217, 72, 65, 0.14);
      color: #7a1d18;
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
      background: rgba(255,255,255,0.78);
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
      background: rgba(255,255,255,0.7);
    }

    .checkbox-row input {
      width: auto;
      margin-top: 2px;
    }

    .mono {
      white-space: pre-wrap;
      font: 500 0.9rem/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
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
      <a href="#outlier">Outlier</a>
      <a href="#discovery">Discovery</a>
      <a href="#theme">Theme</a>
      <a href="#angles">Angles</a>
      <a href="#create">Create</a>
      <a href="#quick">Quick Script</a>
    </nav>

    <section class="grid">
      <section class="section" id="outlier">
        <h2>Outlier Search</h2>
        <p>Single-term search with optional AI insights. Select results here and reuse them in downstream workflows.</p>
        <form id="outlier-form" class="controls">
          <label class="field">
            <span class="field-label">Topic</span>
            <input id="outlier-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <label class="field">
            <span class="field-label">Minimum Outliers</span>
            <input id="outlier-limit" type="number" min="1" max="20" value="10" placeholder="Limit">
          </label>
          <label class="checkbox-inline full"><input id="outlier-insights" type="checkbox" checked><span>Include AI insights</span></label>
          <button class="full" type="submit">Run Outlier Search</button>
        </form>
        <div class="status" id="outlier-status">Run this first if you want theme, angles, or create to reuse the same source set.</div>
        <div class="output" id="outlier-output"></div>
      </section>

      <section class="section" id="discovery">
        <h2>Discovery</h2>
        <p>Multi-term search that collates outliers across several topics into one report.</p>
        <form id="discovery-form" class="controls one-col">
          <textarea id="discovery-terms" placeholder="claude code, cursor ai, github copilot">claude code, cursor ai</textarea>
          <button type="submit">Run Discovery</button>
        </form>
        <div class="status" id="discovery-status"></div>
        <div class="output" id="discovery-output"></div>
      </section>

      <section class="section" id="theme">
        <h2>Theme</h2>
        <p>Find recurring patterns, title moves, and audience intent across the latest outlier set.</p>
        <form id="theme-form" class="controls">
          <label class="field full">
            <span class="field-label">Topic</span>
            <input id="theme-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <button class="full" type="submit">Analyze Theme</button>
        </form>
        <div class="status" id="theme-status"></div>
        <div class="output" id="theme-output"></div>
      </section>

      <section class="section" id="angles">
        <h2>Angles</h2>
        <p>Synthesize angle ideas. If you selected outliers above, this uses those first.</p>
        <form id="angles-form" class="controls">
          <label class="field full">
            <span class="field-label">Topic</span>
            <input id="angles-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <button class="full" type="submit">Generate Angles</button>
        </form>
        <div class="status" id="angles-status"></div>
        <div class="output" id="angles-output"></div>
      </section>

      <section class="section" id="create">
        <h2>Create Script</h2>
        <p>Runs the full creation pipeline in non-interactive mode. If selected outliers exist, their angles seed the run.</p>
        <form id="create-form" class="controls">
          <label class="field">
            <span class="field-label">Topic</span>
            <input id="create-topic" type="text" value="AI agents" placeholder="Topic">
          </label>
          <label class="field">
            <span class="field-label">Duration (Minutes)</span>
            <input id="create-duration" type="number" min="1" max="60" value="11" placeholder="Duration">
          </label>
          <label class="field">
            <span class="field-label">Research Strategy</span>
            <select id="create-strategy">
              <option value="outliers">Outliers</option>
              <option value="top_performers">Top Performers</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">Videos To Analyze</span>
            <input id="create-top-n" type="number" min="1" max="30" value="10" placeholder="Videos to analyze">
          </label>
          <label class="field full">
            <span class="field-label">Notes</span>
            <textarea id="create-notes" class="full" placeholder="Your rough notes">Target business leaders. Explain why AI agents matter now, where teams waste time, and what practical first use cases look like.</textarea>
          </label>
          <button class="full" type="submit">Create Script</button>
        </form>
        <div class="status" id="create-status"></div>
        <div class="output" id="create-output"></div>
      </section>

      <section class="section" id="quick">
        <h2>Quick Script</h2>
        <p>Checklist-driven script generation directly from notes with no outlier research required.</p>
        <form id="quick-form" class="controls">
          <label class="field">
            <span class="field-label">Topic</span>
            <input id="quick-topic" type="text" value="AI agents for ops teams" placeholder="Topic">
          </label>
          <label class="field">
            <span class="field-label">Duration (Minutes)</span>
            <input id="quick-duration" type="number" min="1" max="60" value="8" placeholder="Duration">
          </label>
          <label class="field">
            <span class="field-label">Reading Level</span>
            <input id="quick-reading-level" type="text" value="10th grade" placeholder="Reading level">
          </label>
          <label class="field">
            <span class="field-label">Audience</span>
            <input id="quick-audience" type="text" value="business person" placeholder="Audience">
          </label>
          <label class="field full">
            <span class="field-label">Detailed Notes</span>
            <textarea id="quick-notes" class="full" placeholder="Detailed notes">Explain AI agents in simple language, give 3 concrete team use cases, include one caution about bad automation, and end with a practical starting point.</textarea>
          </label>
          <button class="full" type="submit">Generate Quick Script</button>
        </form>
        <div class="status" id="quick-status"></div>
        <div class="output" id="quick-output"></div>
      </section>
    </section>

    <section class="hero footer">
      <p class="footer-copy">
        This app fronts the current workflow: outlier search, discovery, theme, angles, create, and quick-script.
        Use Outlier first if you want Theme, Angles, and Create to reuse the same source set.
      </p>
      <div class="footer-actions">
        <a class="button-link secondary" href="/docs">API Docs</a>
        <a class="button-link secondary" href="/api">Raw API Index</a>
        <a class="button-link secondary" href="/home">Overview</a>
      </div>
    </section>
  </main>

  <script>
    const state = {
      latestOutliers: [],
      selectedUrls: new Set(),
      activeOutlierJobId: null,
      outlierPollTimer: null,
      activeDiscoveryJobId: null,
      discoveryPollTimer: null
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

    function syncTopicFields(topic) {
      for (const id of ["theme-topic", "angles-topic", "create-topic"]) {
        const input = document.getElementById(id);
        if (input) input.value = topic;
      }
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
                    <div class="stat"><span class="stat-label">Subscribers</span><span class="stat-value">${item.subscribers ? formatNumber(item.subscribers) : "N/A"}</span></div>
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

    function stopDiscoveryPolling() {
      if (state.discoveryPollTimer) {
        clearInterval(state.discoveryPollTimer);
        state.discoveryPollTimer = null;
      }
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

    function renderDiscovery(items, reportName) {
      if (!items || !items.length) {
        return '<p class="meta">No discovery results returned.</p>';
      }
      return `
        <div class="cards">
          <div class="meta">Report: ${escapeHtml(reportName || "N/A")} | Results: ${items.length}</div>
          ${items.slice(0, 12).map((item) => `
            <div class="card">
              <span class="tag">${item.ratio.toFixed(2)}x outlier</span>
              <h3 class="title">${escapeHtml(item.title)}</h3>
              <p class="meta">${escapeHtml(item.channel || "Unknown channel")}</p>
            </div>
          `).join("")}
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
          setStatus("discovery-status", `Loaded ${data.result?.count || 0} discovery results.`);
          setOutputHtml("discovery-output", renderDiscovery(data.result?.results || [], data.result?.report_name));
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

    function renderTheme(result) {
      if (!result || result.error) {
        return `<p class="meta">${escapeHtml(result?.error || "Theme analysis failed.")}</p>`;
      }
      const themes = result.themes || {};
      return `
        <div class="card">
          <span class="tag">${escapeHtml(result.topic || "Theme")}</span>
          <ul class="summary-list">
            <li><strong>Audience intent:</strong> ${escapeHtml(themes.audience_intent || "N/A")}</li>
            <li><strong>Common title phrases:</strong> ${escapeHtml((themes.common_title_phrases || []).join(", ") || "N/A")}</li>
            <li><strong>Recurring topics:</strong> ${escapeHtml((themes.recurring_topics || []).join(", ") || "N/A")}</li>
            <li><strong>Success patterns:</strong> ${escapeHtml((themes.success_criteria_patterns || []).join(", ") || "N/A")}</li>
          </ul>
        </div>
      `;
    }

    function renderAngles(result) {
      const angles = result?.angles || [];
      if (!angles.length) {
        return '<p class="meta">No angles returned.</p>';
      }
      return `
        <div class="cards">
          ${angles.map((angle) => `
            <div class="card">
              <span class="tag">${escapeHtml(String(angle.estimated_performance || 0))}/10</span>
              <h3 class="title">${escapeHtml(angle.angle_name || "Angle")}</h3>
              <p class="meta">${escapeHtml(angle.description || "")}</p>
              <p class="meta"><strong>Why it works:</strong> ${escapeHtml(angle.why_it_works || "")}</p>
            </div>
          `).join("")}
        </div>
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
      const includeInsights = document.getElementById("outlier-insights").checked;
      syncTopicFields(query);
      stopOutlierPolling();
      setStatus("outlier-status", `Running outlier search for "${query}"...`);
      setOutputHtml("outlier-output", renderOutlierProgress([`[*] Queuing outlier search for "${query}"...`]));

      try {
        const job = await postJson("/api/v1/app/outlier/start", { query, limit, include_insights: includeInsights });
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
        setStatus("theme-status", `Theme analysis complete for "${topic}".`);
        setOutputHtml("theme-output", renderTheme(data));
      } catch (error) {
        setStatus("theme-status", error.message || "Theme failed.");
        setOutputHtml("theme-output", `<p class="meta">${escapeHtml(error.message || "Theme failed.")}</p>`);
      }
    });

    document.getElementById("angles-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const topic = document.getElementById("angles-topic").value.trim();
      const chosen = selectedOutliers();
      const videos = chosen.length ? chosen : state.latestOutliers;
      setStatus("angles-status", `Generating angles for "${topic}"...`);
      setOutputHtml("angles-output", '<p class="meta">Synthesizing angles...</p>');
      try {
        const data = await postJson("/api/v1/app/angles", { topic, videos: videos.length ? videos : null });
        setStatus("angles-status", `Generated ${(data.angles || []).length} angles.`);
        setOutputHtml("angles-output", renderAngles(data));
      } catch (error) {
        setStatus("angles-status", error.message || "Angles failed.");
        setOutputHtml("angles-output", `<p class="meta">${escapeHtml(error.message || "Angles failed.")}</p>`);
      }
    });

    document.getElementById("create-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const topic = document.getElementById("create-topic").value.trim();
      const notes = document.getElementById("create-notes").value;
      const duration = Number(document.getElementById("create-duration").value || 11);
      const strategy = document.getElementById("create-strategy").value;
      const topN = Number(document.getElementById("create-top-n").value || 10);
      const selectedVideos = selectedOutliers();
      setStatus("create-status", `Running full create workflow for "${topic}"...`);
      setOutputHtml("create-output", '<p class="meta">This can take a few minutes...</p>');
      try {
        const data = await postJson("/api/v1/app/create", {
          topic,
          notes,
          duration,
          strategy,
          top_n_outliers: topN,
          selected_videos: selectedVideos.length ? selectedVideos : null
        }, 600000);
        setStatus("create-status", `Script created. Quality score: ${data.quality_report?.overall_score ?? "N/A"}/100`);
        setOutputHtml("create-output", renderScriptResult(data, true));
      } catch (error) {
        setStatus("create-status", error.message || "Create failed.");
        setOutputHtml("create-output", `<p class="meta">${escapeHtml(error.message || "Create failed.")}</p>`);
      }
    });

    document.getElementById("quick-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const topic = document.getElementById("quick-topic").value.trim();
      const notes = document.getElementById("quick-notes").value;
      const duration = Number(document.getElementById("quick-duration").value || 8);
      const readingLevel = document.getElementById("quick-reading-level").value.trim();
      const audience = document.getElementById("quick-audience").value.trim();
      setStatus("quick-status", `Generating quick script for "${topic}"...`);
      setOutputHtml("quick-output", '<p class="meta">Generating and scoring script...</p>');
      try {
        const data = await postJson("/api/v1/app/quick-script", {
          topic,
          notes,
          duration,
          reading_level: readingLevel,
          audience
        }, 600000);
        setStatus("quick-status", `Quick script complete. Quality score: ${data.quality_report?.overall_score ?? "N/A"}/100`);
        setOutputHtml("quick-output", renderScriptResult(data, true));
      } catch (error) {
        setStatus("quick-status", error.message || "Quick script failed.");
        setOutputHtml("quick-output", `<p class="meta">${escapeHtml(error.message || "Quick script failed.")}</p>`);
      }
    });

  </script>
</body>
</html>
"""
