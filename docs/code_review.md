# Code Review Report

Comprehensive review of the entire repository covering backend, frontend, infrastructure, and tests.

## Critical

### 1. Session cookie is forgeable (backend/app/main.py)
The session cookie (`pm_session`) is set to the raw username string. Any client can forge authentication by manually setting `pm_session=user` -- no password required. There is no server-side session store validating that the cookie was issued by the server.

**Action:** Generate a random session token on login, store it server-side (e.g., in a dict or DB table), and validate incoming cookies against that store.

### 2. Plaintext password storage (backend/app/main.py)
The `users` table stores `password_plaintext` and comparison uses `==`. If the SQLite file is exposed, all credentials are readable.

**Action:** Use `bcrypt` or `argon2` for password hashing, even for the MVP seeded user.

## High

### 3. Unbounded chat history -- memory leak and token overflow (backend/app/main.py)
`SESSION_CHAT_HISTORY` grows without limit. Over time this consumes unbounded memory and will cause OpenAI requests to exceed token limits.

**Action:** Cap history to the last N message pairs (e.g., 20) or implement a token budget check before sending to OpenAI.

### 4. No timeout on OpenAI API calls (backend/app/ai_client.py)
Neither `run_connectivity_check` nor `run_structured_chat` set a timeout. A slow or hanging OpenAI response blocks the worker thread indefinitely.

**Action:** Pass a `timeout` parameter to the OpenAI client (e.g., 30 seconds).

### 5. Side effect inside React state updater (frontend/src/components/KanbanBoard.tsx)
`persistBoard()` is called inside `setBoard`'s updater function. React updater functions must be pure -- side effects here can fire multiple times in StrictMode or concurrent mode.

**Action:** Move `persistBoard` outside the updater. Compute the next state, call `setBoard(next)`, then call `persistBoard(next)` separately.

### 6. No debounce on board persistence -- rapid PUTs race (frontend/src/components/KanbanBoard.tsx)
Every keystroke in column rename and every drag fires a PUT. Rapid mutations cause concurrent requests where an earlier state can overwrite a later one (last-write-wins).

**Action:** Debounce `persistBoard` (e.g., 500ms) or use an abort controller to cancel stale requests.

### 7. Potential crash when card ID has no matching entry (frontend/src/components/KanbanBoard.tsx)
`column.cardIds.map((cardId) => board.cards[cardId])` produces `undefined` if a card was deleted from the cards map but its ID remains in a column's `cardIds` array. This crashes downstream components.

**Action:** Filter out undefined entries: `column.cardIds.map(id => board.cards[id]).filter(Boolean)`.

### 8. Path traversal risk in frontend file serving (backend/app/main.py)
`_frontend_file` does not verify that the resolved path stays within `FRONTEND_DIST_DIR`. A crafted path could potentially escape the intended directory.

**Action:** Add `candidate.resolve().is_relative_to(FRONTEND_DIST_DIR.resolve())` check.

### 9. Silent failure when AI board operations fail (backend/app/main.py)
When `_apply_board_operations` raises `ValueError`, the error is caught silently with no logging and no user-facing explanation. The AI tells the user "I moved your card" but nothing happened.

**Action:** Return the validation error message in the response so the frontend can display it. Add logging for diagnostics.

### 10. Dockerfile runs as root
The final image has no `USER` directive. The uvicorn process runs as root inside the container.

**Action:** Add a non-root user and switch to it before the `CMD`.

### 11. `.env` not excluded from Docker build context
The `.env` file (containing the real OpenAI API key) is sent to the Docker daemon during build. It could leak in CI logs or layer caches.

**Action:** Add `.env` to `.dockerignore`.

## Medium

### 12. No CSRF protection on POST endpoints (backend/app/main.py)
Login and logout forms use POST with no CSRF token. An attacker could craft a page that submits these forms on behalf of a user.

**Action:** Add CSRF tokens to forms, or use `SameSite=strict` cookies (currently `lax`).

### 13. `_write_user_board` checks `rowcount` outside the `with` block (backend/app/main.py)
The cursor's `rowcount` is read after the `with _db_connection()` block exits and the connection is closed. This relies on SQLite cursor implementation detail.

**Action:** Move the `rowcount` check inside the `with` block.

### 14. `loadBoardForRefresh` failure loses the assistant reply (frontend/src/components/KanbanBoard.tsx)
If the board refresh fetch fails after a successful chat response, the outer catch block fires and the user sees an error message. The assistant's reply is lost even though the chat succeeded.

**Action:** Separate error handling for the chat call and the board refresh. Always display the assistant's message if it was received.

### 15. No focus trap or Escape-to-close on chat drawer (frontend/src/components/KanbanBoard.tsx)
When the chat drawer is open, keyboard users can tab behind it. Pressing Escape does nothing.

**Action:** Add a focus trap when the drawer is open and close it on Escape keypress.

### 16. Form inputs lack accessible labels (frontend/src/components/NewCardForm.tsx)
The `<input>` and `<textarea>` use `placeholder` as their only labels. Placeholder text is not reliably announced by screen readers.

**Action:** Add `aria-label` attributes or visible `<label>` elements.

### 17. Column rename inputs share identical aria-labels (frontend/src/components/KanbanColumn.tsx)
All five columns use `aria-label="Column title"`. Screen reader users cannot distinguish which column they are editing.

**Action:** Use `aria-label={`Title for ${column.title}`}` or similar.

### 18. Duplicated test helpers across all backend test files (backend/tests/)
`_make_client`, `_login`, and `_FakeOpenAIClient` are copy-pasted into every test file (~40 lines of duplication).

**Action:** Create a `conftest.py` with shared fixtures.

### 19. `sys.path.insert` hack in every test file (backend/tests/)
Every test file manually inserts the parent directory into `sys.path`.

**Action:** Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` in `pyproject.toml`.

### 20. Test globals mutated without cleanup (backend/tests/)
`main.FRONTEND_DIST_DIR` and `main.DB_PATH` are reassigned in every test's `_make_client`. If tests run in parallel or fail mid-setup, state leaks.

**Action:** Use `monkeypatch` fixtures for module-level globals.

### 21. No `secure` flag on cookies (backend/app/main.py)
Both `set_cookie` calls omit `secure=True`. Over HTTPS, cookies would still be sent over plain HTTP.

**Action:** Set `secure=True` when running behind HTTPS. For local dev, this can remain off but should be configurable.

### 22. Bare `except Exception` in chat endpoint (backend/app/main.py)
All exceptions from AI response parsing are caught and mapped to HTTP 502. This masks genuine bugs (Pydantic validation errors, internal logic errors) that should be 500s.

**Action:** Catch specific expected exceptions (`json.JSONDecodeError`, `ValidationError`) separately from unexpected ones.

### 23. Sync blocking OpenAI calls (backend/app/ai_client.py)
Both AI functions are synchronous and make HTTP calls. FastAPI runs them in its threadpool, limiting concurrency to threadpool size.

**Action:** Convert to `async` using the async OpenAI client for better concurrency.

## Low

### 24. `cardsById` useMemo is a no-op (frontend/src/components/KanbanBoard.tsx)
`useMemo(() => board.cards, [board.cards])` performs no computation. The memo wrapper provides zero benefit.

**Action:** Remove the `useMemo` wrapper; use `board.cards` directly.

### 25. Chat messages keyed by array index (frontend/src/components/KanbanBoard.tsx)
Using index as part of the React key is fragile if messages are ever reordered or removed.

**Action:** Assign a unique ID to each message when created.

### 26. `createId` uses `Math.random()` (frontend/src/lib/kanban.ts)
Only ~31 bits of entropy. `crypto.randomUUID()` would be simpler and more robust.

**Action:** Replace with `crypto.randomUUID()`.

### 27. No error boundary wrapping the app (frontend/src/app/page.tsx)
If `KanbanBoard` throws during render, the entire page crashes with no recovery UI.

**Action:** Add a React error boundary around `KanbanBoard`.

### 28. E2E tests only run in Chromium (frontend/playwright.config.ts)
No Firefox or WebKit projects configured. Cross-browser issues will be missed.

**Action:** Add Firefox and WebKit projects when ready to expand test coverage.

### 29. Mac and Linux scripts are identical (scripts/)
`start-mac.sh` and `start-linux.sh` are byte-for-byte identical, as are the stop scripts.

**Action:** Consolidate into `start.sh` and `stop.sh` to reduce maintenance.

### 30. Scripts assume execution from repo root (scripts/)
`$(pwd)` is used for `DATA_DIR`. Running from another directory mounts the wrong volume.

**Action:** Derive paths from script location: `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`.

### 31. Dockerfile layer caching is suboptimal
`COPY backend/ ./` before `uv sync` busts the dependency cache on every code change.

**Action:** Copy `pyproject.toml` and `uv.lock` first, run `uv sync`, then copy source.

## Test Coverage Gaps

| Area | Missing Coverage |
|------|-----------------|
| Session forgery | No test that setting `pm_session=user` cookie without login grants access |
| Cookie flags | No test asserting `httponly` and `samesite` are set |
| Empty chat prompt | `ChatMessagePayload` rejects empty prompts but no test covers it |
| Malformed AI JSON | No test for `json.loads` failure on OpenAI response |
| Chat history bounds | No test verifying history is bounded or cleaned up |
| Board fetch failure | Frontend fallback to `initialData` on API error is untested |
| 401 redirect | `window.location.assign("/login")` path is untested |
| Chat error handling | `handleChatSubmit` catch block is untested |
| `createId` | No unit tests for format or uniqueness |
| `moveCard` edge cases | Missing: same-column reorder, invalid IDs, single-card columns |
| NewCardForm | No unit tests for validation, cancel, or form reset |
| KanbanCard | No unit tests for delete callback or drag states |
| KanbanColumn | Only indirectly tested through KanbanBoard tests |
