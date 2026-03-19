def render_home_app() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Analysis App</title>
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
      width: min(1160px, calc(100vw - 32px));
      margin: 36px auto;
    }

    .hero, .section {
      border-radius: 28px;
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .hero {
      padding: 30px;
    }

    h1 {
      margin: 0;
      max-width: 11ch;
      line-height: 0.95;
      letter-spacing: -0.05em;
      font-size: clamp(2.4rem, 5vw, 4.8rem);
    }

    .subhead {
      margin: 14px 0 0;
      max-width: 52rem;
      color: var(--muted);
      font: 500 1rem/1.65 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 24px;
    }

    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 52px;
      padding: 0 18px;
      border-radius: 18px;
      text-decoration: none;
      font: 700 0.96rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .button-primary {
      color: white;
      background: linear-gradient(135deg, var(--accent), #b8322b);
      box-shadow: 0 12px 24px rgba(217, 72, 65, 0.28);
    }

    .button-secondary {
      color: var(--ink);
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid var(--line);
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 18px;
    }

    .section {
      padding: 22px;
    }

    .section h2 {
      margin: 0 0 8px;
      font-size: 1.5rem;
    }

    .section p {
      margin: 0 0 14px;
      color: var(--muted);
      font: 500 0.96rem/1.6 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    ul {
      margin: 0;
      padding-left: 18px;
      color: var(--ink);
      font: 500 0.95rem/1.7 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    li + li {
      margin-top: 8px;
    }

    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.92em;
    }

    @media (max-width: 860px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>YouTube outlier analysis, minus the broken parts.</h1>
      <p class="subhead">
        This web app currently supports regular YouTube outlier search and the API tools around it.
        Shorts has been removed. Script generation and research workflows remain CLI-only.
      </p>
      <div class="actions">
        <a class="button button-primary" href="/outliers">Open Outlier Explorer</a>
        <a class="button button-secondary" href="/docs">Open API Docs</a>
      </div>
    </section>

    <section class="grid">
      <section class="section">
        <h2>Web Features</h2>
        <p>These work directly in the browser today.</p>
        <ul>
          <li><code>/outliers</code>: search a topic and view ranked regular YouTube outliers.</li>
          <li><code>/docs</code>: Swagger UI for all API endpoints.</li>
          <li><code>/api/v1/outliers/direct</code>: fast direct outlier search for UI use.</li>
          <li><code>/api/v1/search/outliers</code>: async search job creation.</li>
          <li><code>/api/v1/jobs</code> and <code>/api/v1/jobs/&lt;job_id&gt;</code>: inspect job status and results.</li>
          <li><code>/api/v1/videos/mark</code>, <code>/api/v1/videos/marked</code>, and <code>/api/v1/shortlist/analyze</code>: mark videos and run follow-up analysis after an async search populates the database.</li>
        </ul>
      </section>

      <section class="section">
        <h2>CLI-Only Features</h2>
        <p>These exist in the project, but are not exposed as browser pages.</p>
        <ul>
          <li><code>python3.10 main.py discovery "term 1, term 2"</code></li>
          <li><code>python3.10 main.py angles "topic"</code></li>
          <li><code>python3.10 main.py theme "topic"</code></li>
          <li><code>python3.10 main.py create "topic" --notes "..."</code></li>
          <li><code>python3.10 main.py quick-script "topic" --notes "..."</code></li>
        </ul>
      </section>
    </section>
  </main>
</body>
</html>
"""
