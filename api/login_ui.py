from urllib.parse import quote


def render_login_ui(next_path: str = "/", error: str = "", configured: bool = True) -> str:
    safe_next = quote(next_path or "/", safe="/?=&-%")
    error_html = ""
    if error:
        error_html = f'<p class="notice error">{error}</p>'
    elif not configured:
        error_html = '<p class="notice error">Login is not configured yet. Set APP_LOGIN_PASSWORD and APP_SESSION_SECRET on the server.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Strategy OS Login</title>
  <style>
    :root {{
      --bg: #f4efe7;
      --surface: rgba(255, 252, 246, 0.94);
      --ink: #1f2933;
      --muted: #5b6770;
      --accent: #d94841;
      --line: rgba(31, 41, 51, 0.12);
      --shadow: 0 22px 58px rgba(84, 67, 48, 0.16);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(217, 72, 65, 0.18), transparent 32%),
        radial-gradient(circle at left 20%, rgba(31, 41, 51, 0.08), transparent 28%),
        linear-gradient(180deg, #f8f4ed 0%, var(--bg) 100%);
      padding: 20px;
    }}

    .card {{
      width: min(460px, 100%);
      border-radius: 28px;
      border: 1px solid var(--line);
      background: var(--surface);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      padding: 28px 24px;
    }}

    h1 {{
      margin: 0 0 10px;
      line-height: 1;
      letter-spacing: -0.04em;
      font-size: clamp(1.6rem, 4vw, 2.4rem);
    }}

    p {{
      margin: 0;
      color: var(--muted);
      font: 500 0.98rem/1.65 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }}

    form {{
      margin-top: 20px;
      display: grid;
      gap: 12px;
    }}

    label {{
      display: grid;
      gap: 8px;
    }}

    .field-label {{
      color: var(--muted);
      font: 700 0.78rem/1 "Helvetica Neue", Helvetica, Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    input, button {{
      width: 100%;
      border-radius: 14px;
      font-size: 0.96rem;
      padding: 13px 14px;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }}

    input {{
      border: 1px solid var(--line);
      color: var(--ink);
      background: rgba(255, 255, 255, 0.86);
    }}

    button {{
      margin-top: 4px;
      border: none;
      cursor: pointer;
      color: white;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), #b8322b);
      box-shadow: 0 10px 24px rgba(217, 72, 65, 0.2);
    }}

    .notice {{
      margin-top: 16px;
      padding: 11px 13px;
      border-radius: 14px;
      font: 600 0.9rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
    }}

    .error {{
      background: rgba(217, 72, 65, 0.12);
      color: #8d231d;
    }}

    .meta {{
      margin-top: 16px;
      font-size: 0.88rem;
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1>YouTube Strategy OS</h1>
    <p>Private workspace login for the research and scripting app.</p>
    {error_html}
    <form id="login-form">
      <input id="login-next" type="hidden" value="{safe_next}">
      <label>
        <span class="field-label">Password</span>
        <input id="login-password" type="password" autocomplete="current-password" placeholder="Enter shared password">
      </label>
      <button type="submit">Login</button>
    </form>
    <p class="meta">Use a strong shared password and keep the app behind HTTPS in production.</p>
  </main>

  <script>
    const form = document.getElementById("login-form");
    const passwordInput = document.getElementById("login-password");
    const nextInput = document.getElementById("login-next");

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      const password = passwordInput.value.trim();
      if (!password) {{
        passwordInput.focus();
        return;
      }}

      try {{
        const response = await fetch("/api/v1/auth/login", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{
            password,
            next: decodeURIComponent(nextInput.value || "/")
          }})
        }});

        const data = await response.json();
        if (!response.ok) {{
          throw new Error(data.detail || "Login failed");
        }}

        window.location.href = data.next || "/";
      }} catch (error) {{
        window.location.href = "/login?error=" + encodeURIComponent(error.message) + "&next=" + encodeURIComponent(decodeURIComponent(nextInput.value || "/"));
      }}
    }});
  </script>
</body>
</html>"""
