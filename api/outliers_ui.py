def render_outliers_app() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Outlier Explorer</title>
  <style>
    :root {
      --bg: #f4efe7;
      --surface: rgba(255, 252, 246, 0.9);
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
      width: min(1140px, calc(100vw - 32px));
      margin: 36px auto;
    }

    .panel {
      border-radius: 28px;
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      padding: 28px;
    }

    h1 {
      margin: 0;
      max-width: 11ch;
      line-height: 0.95;
      letter-spacing: -0.05em;
      font-size: clamp(2.3rem, 5vw, 4.6rem);
    }

    .subhead {
      margin: 14px 0 0;
      max-width: 50rem;
      color: var(--muted);
      font: 500 1rem/1.65 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .toolbar {
      display: grid;
      grid-template-columns: 1fr 120px 160px;
      gap: 12px;
      margin-top: 26px;
    }

    input, button {
      padding: 16px 18px;
      font-size: 1rem;
      border-radius: 18px;
    }

    input {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.82);
      color: var(--ink);
    }

    button {
      border: none;
      cursor: pointer;
      color: white;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), #b8322b);
      box-shadow: 0 12px 24px rgba(217, 72, 65, 0.28);
    }

    .status {
      min-height: 24px;
      margin-top: 16px;
      color: var(--muted);
      font: 500 0.95rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .results {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-top: 22px;
    }

    .card {
      border-radius: 20px;
      padding: 18px;
      background: rgba(255, 255, 255, 0.76);
      border: 1px solid rgba(31, 41, 51, 0.08);
      box-shadow: 0 12px 26px rgba(31, 41, 51, 0.08);
    }

    .pill {
      display: inline-flex;
      padding: 6px 10px;
      border-radius: 999px;
      color: #7a1d18;
      background: rgba(217, 72, 65, 0.14);
      font: 700 0.78rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .title {
      margin: 10px 0 8px;
      font-size: 1.12rem;
      line-height: 1.28;
    }

    .meta {
      margin: 0;
      color: var(--muted);
      font: 500 0.92rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .stat {
      padding: 10px;
      border-radius: 14px;
      background: rgba(244, 239, 231, 0.8);
    }

    .label {
      display: block;
      font-size: 0.76rem;
      color: var(--muted);
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .value {
      display: block;
      margin-top: 6px;
      font-weight: 700;
    }

    .link {
      display: inline-block;
      margin-top: 12px;
      color: var(--accent);
      text-decoration: none;
      font: 700 0.9rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .empty {
      color: var(--muted);
      font: 500 0.95rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
      margin: 0;
    }

    @media (max-width: 820px) {
      .toolbar {
        grid-template-columns: 1fr;
      }
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="panel">
      <h1>Find the current YouTube outliers for a topic.</h1>
      <p class="subhead">
        This is the working browser UI for the app right now. It uses the same regular outlier logic
        as the CLI and ranks videos by how far they outperform the creator's normal baseline.
      </p>
      <form class="toolbar" id="search-form">
        <input id="topic" type="text" value="AI agents" placeholder="Try: AI agents, coding, productivity">
        <input id="limit" type="number" min="1" max="20" value="8">
        <button type="submit">Find Outliers</button>
      </form>
      <div class="status" id="status">Loading starts as soon as the page opens.</div>
      <section class="results" id="results"></section>
    </section>
  </main>

  <script>
    const form = document.getElementById("search-form");
    const topicInput = document.getElementById("topic");
    const limitInput = document.getElementById("limit");
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    function formatNumber(value) {
      return new Intl.NumberFormat().format(value || 0);
    }

    function renderCard(item) {
      return `
        <article class="card">
          <span class="pill">${item.ratio.toFixed(2)}x outlier</span>
          <h2 class="title">${item.title || "Untitled video"}</h2>
          <p class="meta">${item.channel || "Unknown channel"}</p>
          <div class="stats">
            <div class="stat">
              <span class="label">Views</span>
              <span class="value">${formatNumber(item.views)}</span>
            </div>
            <div class="stat">
              <span class="label">Median</span>
              <span class="value">${formatNumber(Math.round(item.median_views || 0))}</span>
            </div>
            <div class="stat">
              <span class="label">Subscribers</span>
              <span class="value">${item.subscribers ? formatNumber(item.subscribers) : "N/A"}</span>
            </div>
          </div>
          <a class="link" href="${item.url}" target="_blank" rel="noreferrer">Open on YouTube</a>
        </article>
      `;
    }

    function renderLoading(label) {
      results.innerHTML = `<p class="empty">${label}</p>`;
    }

    async function fetchJson(url, timeoutMs = 90000) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(url, { signal: controller.signal });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Request failed");
        }
        return data;
      } finally {
        clearTimeout(timer);
      }
    }

    async function loadOutliers(query, limit) {
      status.textContent = `Loading regular YouTube outliers for "${query}"...`;
      renderLoading("Scanning YouTube and comparing channel baselines...");

      try {
        const data = await fetchJson(`/api/v1/outliers/direct?query=${encodeURIComponent(query)}&limit=${limit}`);
        if (!data.results || !data.results.length) {
          status.textContent = `No outliers found for "${query}".`;
          results.innerHTML = `<p class="empty">Try a broader topic or lower the threshold in config.</p>`;
          return;
        }

        status.textContent = `Loaded ${data.count} outliers for "${data.query}".`;
        results.innerHTML = data.results.map(renderCard).join("");
      } catch (error) {
        status.textContent = error.message || "Search failed.";
        results.innerHTML = `<p class="empty">${status.textContent}</p>`;
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const query = topicInput.value.trim();
      const limit = Number(limitInput.value || 8);
      if (!query) {
        status.textContent = "Topic is required.";
        return;
      }
      loadOutliers(query, limit);
    });

    window.addEventListener("load", () => {
      loadOutliers(topicInput.value.trim(), Number(limitInput.value || 8));
    });
  </script>
</body>
</html>
"""
