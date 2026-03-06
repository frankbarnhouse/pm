from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Project Management MVP API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Project Management MVP</title>
    <style>
      :root {
        --accent-yellow: #ecad0a;
        --primary-blue: #209dd7;
        --secondary-purple: #753991;
        --navy-dark: #032147;
        --gray-text: #888888;
      }
      body {
        margin: 0;
        font-family: "Segoe UI", sans-serif;
        color: var(--navy-dark);
        background: linear-gradient(165deg, #f9fbff 0%, #eef5ff 100%);
      }
      main {
        max-width: 760px;
        margin: 64px auto;
        padding: 28px;
        background: #ffffff;
        border: 1px solid rgba(3, 33, 71, 0.08);
        border-radius: 16px;
        box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
      }
      h1 {
        margin-top: 0;
      }
      .tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(32, 157, 215, 0.14);
        color: var(--primary-blue);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .status {
        margin-top: 24px;
        padding: 14px;
        border-radius: 12px;
        background: #f7f8fb;
        border: 1px solid rgba(3, 33, 71, 0.08);
        color: var(--gray-text);
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        white-space: pre-wrap;
      }
      button {
        margin-top: 16px;
        border: 0;
        border-radius: 999px;
        padding: 10px 18px;
        background: var(--secondary-purple);
        color: #fff;
        font-weight: 700;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <main>
      <span class=\"tag\">Single Container Smoke Test</span>
      <h1>Hello from FastAPI</h1>
      <p>This page is temporary scaffolding for Part 2.</p>
      <p>Click the button to test an API call to <code>/api/health</code>.</p>
      <button id=\"run-check\" type=\"button\">Call API</button>
      <pre class=\"status\" id=\"status\">Waiting for API call...</pre>
    </main>
    <script>
      const button = document.getElementById("run-check");
      const status = document.getElementById("status");

      button.addEventListener("click", async () => {
        status.textContent = "Loading /api/health...";
        try {
          const response = await fetch("/api/health");
          const payload = await response.json();
          status.textContent = JSON.stringify(payload, null, 2);
        } catch (error) {
          status.textContent = `Request failed: ${error}`;
        }
      });
    </script>
  </body>
</html>
"""
