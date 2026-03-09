_SHARED_STYLES = """
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
        background: linear-gradient(165deg, #f9fbff 0%, #eef5ff 100%);
        color: var(--navy-dark);
    }
    main {
        max-width: 420px;
        margin: 88px auto;
        padding: 28px;
        border-radius: 16px;
        border: 1px solid rgba(3, 33, 71, 0.08);
        background: #fff;
        box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
    }
    h1 {
        margin: 0 0 8px;
    }
    p {
        margin: 0 0 18px;
        color: var(--gray-text);
    }
    label {
        display: block;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 700;
    }
    input {
        width: 100%;
        margin-bottom: 14px;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid rgba(3, 33, 71, 0.15);
        box-sizing: border-box;
    }
    button {
        width: 100%;
        border: 0;
        border-radius: 999px;
        padding: 10px 14px;
        color: #fff;
        background: var(--secondary-purple);
        font-weight: 700;
        cursor: pointer;
    }
    button:hover {
        filter: brightness(1.1);
    }
    .hint {
        margin-top: 12px;
        font-size: 12px;
    }
    .error {
        margin-bottom: 12px;
        color: #a22;
        font-weight: 700;
    }
    .link {
        margin-top: 16px;
        text-align: center;
        font-size: 13px;
    }
    .link a {
        color: var(--secondary-purple);
        text-decoration: none;
        font-weight: 600;
    }
    .link a:hover {
        text-decoration: underline;
    }
"""


def login_html(show_error: bool) -> str:
    error_text = (
        "<p class=\"error\">Invalid credentials.</p>"
        if show_error
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Sign In | Kanban Studio</title>
        <style>{_SHARED_STYLES}</style>
    </head>
    <body>
        <main>
            <h1>Sign in</h1>
            <p>Sign in to access your boards.</p>
            {error_text}
            <form method="post" action="/auth/login">
                <label for="username">Username</label>
                <input id="username" name="username" required />
                <label for="password">Password</label>
                <input id="password" name="password" type="password" required />
                <button type="submit">Sign in</button>
            </form>
            <p class="link">No account? <a href="/register">Create one</a></p>
        </main>
    </body>
</html>
"""


def register_html(error_message: str = "") -> str:
    error_text = (
        f"<p class=\"error\">{error_message}</p>"
        if error_message
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Register | Kanban Studio</title>
        <style>{_SHARED_STYLES}</style>
    </head>
    <body>
        <main>
            <h1>Create account</h1>
            <p>Sign up to start managing your projects.</p>
            {error_text}
            <form method="post" action="/auth/register">
                <label for="username">Username</label>
                <input id="username" name="username" minlength="3" maxlength="30" required />
                <label for="display_name">Display name (optional)</label>
                <input id="display_name" name="display_name" maxlength="60" />
                <label for="password">Password</label>
                <input id="password" name="password" type="password" minlength="4" required />
                <button type="submit">Create account</button>
            </form>
            <p class="link">Already have an account? <a href="/login">Sign in</a></p>
        </main>
    </body>
</html>
"""
