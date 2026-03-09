def login_html(show_error: bool) -> str:
    error_text = (
        "<p class=\"error\">Invalid credentials. Use user / password.</p>"
        if show_error
        else ""
    )
    return f"""<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Sign In | Kanban Studio</title>
        <style>
            :root {{
                --accent-yellow: #ecad0a;
                --primary-blue: #209dd7;
                --secondary-purple: #753991;
                --navy-dark: #032147;
                --gray-text: #888888;
            }}
            body {{
                margin: 0;
                font-family: "Segoe UI", sans-serif;
                background: linear-gradient(165deg, #f9fbff 0%, #eef5ff 100%);
                color: var(--navy-dark);
            }}
            main {{
                max-width: 420px;
                margin: 88px auto;
                padding: 28px;
                border-radius: 16px;
                border: 1px solid rgba(3, 33, 71, 0.08);
                background: #fff;
                box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
            }}
            h1 {{
                margin: 0 0 8px;
            }}
            p {{
                margin: 0 0 18px;
                color: var(--gray-text);
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            input {{
                width: 100%;
                margin-bottom: 14px;
                padding: 10px 12px;
                border-radius: 10px;
                border: 1px solid rgba(3, 33, 71, 0.15);
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                border: 0;
                border-radius: 999px;
                padding: 10px 14px;
                color: #fff;
                background: var(--secondary-purple);
                font-weight: 700;
                cursor: pointer;
            }}
            .hint {{
                margin-top: 12px;
                font-size: 12px;
            }}
            .error {{
                margin-bottom: 12px;
                color: #a22;
                font-weight: 700;
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>Sign in</h1>
            <p>Use the MVP credentials to access the board.</p>
            {error_text}
            <form method=\"post\" action=\"/auth/login\">
                <label for=\"username\">Username</label>
                <input id=\"username\" name=\"username\" required />
                <label for=\"password\">Password</label>
                <input id=\"password\" name=\"password\" type=\"password\" required />
                <button type=\"submit\">Sign in</button>
            </form>
            <p class=\"hint\">Username: <strong>user</strong>, Password: <strong>password</strong></p>
        </main>
    </body>
</html>
"""
