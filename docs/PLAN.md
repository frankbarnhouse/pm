# Project Plan

## Working agreements

- [x] Use Part 1 as a hard gate. No implementation for Part 2+ until user approval.
- [x] Keep architecture to a single Docker container for the MVP.
- [x] Keep auth/session simple for MVP.
- [x] Prioritize valuable unit and integration tests; target around 80% unit coverage only when sensible for the scope.
- [x] Propose AI Structured Output schema for user sign-off before implementation.
- [x] Define script filenames and conventions in Part 2.

## Part 1: Planning and documentation gate

### Checklist

- [x] Expand this plan with detailed checklists.
- [x] Add tests and success criteria for each part.
- [x] Create `frontend/AGENTS.md` describing current frontend code.
- [x] User reviews and approves plan before Part 2 starts.

### Tests

- [x] Documentation quality review against business requirements and technical decisions.
- [x] Confirm each part has explicit deliverables, tests, and success criteria.

### Success criteria

- [x] Plan is specific enough to execute without guesswork.
- [x] Scope and ordering are clear and aligned with MVP constraints.
- [x] User explicitly approves moving to Part 2.

## Part 2: Scaffolding (single-container baseline)

### Checklist

- [x] Create backend app scaffold in `backend/` using FastAPI.
- [x] Add Dockerfile and container run strategy for one container serving backend and frontend assets.
- [x] Add basic route `GET /api/health` returning status JSON.
- [x] Add temporary root HTML response (hello world) at `/` to verify backend serving path before frontend integration.
- [x] Define script naming conventions in `scripts/`:
- [x] `scripts/start-mac.sh`
- [x] `scripts/stop-mac.sh`
- [x] `scripts/start-linux.sh`
- [x] `scripts/stop-linux.sh`
- [x] `scripts/start-windows.ps1`
- [x] `scripts/stop-windows.ps1`
- [x] Ensure scripts build/run/stop the same single container consistently.

### Tests

- [x] Container build test: `docker build` succeeds.
- [x] Runtime smoke test: container starts and serves `/` hello world page.
- [x] API smoke test: `GET /api/health` returns expected JSON.
- [x] Script verification on shell level for argument handling and idempotent stop behavior.

### Success criteria

- [x] Project runs locally with one command per OS via scripts.
- [x] Single container serves backend endpoints and root content.
- [x] Scaffolding is clean and minimal, ready for frontend integration.

## Part 3: Serve existing frontend from FastAPI

### Checklist

- [x] Build Next.js frontend as static assets.
- [x] Wire FastAPI to serve built frontend at `/`.
- [x] Keep API namespace under `/api/*`.
- [x] Ensure static asset paths resolve correctly in container.
- [x] Remove temporary hello world route after frontend takeover.

### Tests

- [x] Frontend unit tests pass with sensible coverage for implemented functionality.
- [x] Integration test: root route returns Kanban UI from backend server.
- [x] Integration test: asset files load correctly (no broken JS/CSS references).
- [x] Container smoke test: board visible at `/` after container startup.

### Success criteria

- [x] Existing Kanban demo renders at `/` when run in container.
- [x] API endpoints remain reachable under `/api`.
- [x] Coverage targets are used pragmatically and valuable tests are prioritized.

## Part 4: Simple fake sign-in flow

### Checklist

- [x] Add simple sign-in page/state with fixed credentials (`user` / `password`).
- [x] Add simple session handling (cookie-based session acceptable for MVP).
- [x] Gate Kanban route to signed-in users.
- [x] Add logout action clearing session.
- [x] Keep UX minimal and explicit for invalid credentials.

### Tests

- [x] Unit tests for auth/session helpers and credential validation logic.
- [x] Integration tests for login success/failure and route gating.
- [x] Integration test for logout flow.
- [x] Coverage is reviewed pragmatically based on test value.

### Success criteria

- [x] Unauthenticated users cannot access board route.
- [x] Correct credentials allow access and maintain session.
- [x] Logout reliably returns user to signed-out state.

## Part 5: Database modeling and sign-off

### Checklist

- [x] Propose SQLite schema for users and one board per user.
- [x] Model board storage as JSON payload for columns/cards.
- [x] Document schema, constraints, and migration approach in `docs/`.
- [x] Propose AI output schema draft for later Part 9 sign-off.
- [x] Obtain user sign-off before implementing data layer changes.

### Tests

- [x] Validate schema proposal against required operations (read board, update board, card moves, edits).
- [x] Confirm forward compatibility for multi-user support.

### Success criteria

- [x] Data model is simple, documented, and sufficient for MVP use cases.
- [x] User approves schema decisions before implementation.

### Approved design decisions

- [x] Store MVP login password in plaintext for seeded local dev user (`user` / `password`).
- [x] Board write contract is overwrite-only (`PUT /api/board` replaces full board payload).
- [x] AI-applied board updates must be atomic all-or-nothing after validation.

## Part 6: Backend Kanban API with persistence

### Checklist

- [x] Implement DB initialization on startup if DB file does not exist.
- [x] Add API endpoints for reading and updating board data by user.
- [x] Enforce simple auth/session checks on protected endpoints.
- [x] Keep update contract explicit and validated.
- [x] Add backend service/repository separation only as needed for clarity.

### Tests

- [x] Backend unit tests for DB access and data transformation logic.
- [x] API integration tests for success and error cases.
- [x] Integration test for first-run DB creation path.
- [x] Review backend unit coverage pragmatically; prioritize valuable cases over strict quota.

### Success criteria

- [x] Board state persists across restarts.
- [x] API behavior is deterministic and documented.
- [x] DB is auto-created without manual steps.

## Part 7: Connect frontend to backend API

### Checklist

- [x] Replace frontend in-memory board state initialization with backend fetch.
- [x] Persist board mutations through backend API.
- [x] Handle loading and failure states with minimal UI feedback.
- [x] Preserve drag/drop and card edit/create/delete behavior.

### Tests

- [x] Frontend unit tests for API client and state transitions.
- [x] Integration tests covering read-on-load and mutate-then-refresh flows.
- [x] End-to-end test for persistence across page reload.
- [x] Review frontend unit coverage pragmatically; prioritize valuable cases over strict quota.

### Success criteria

- [x] UI reflects persisted backend state, not local demo-only state.
- [x] Core Kanban interactions continue to work with API-backed data.

## Part 8: OpenAI connectivity validation

### Checklist

- [x] Add backend OpenAI client wiring using `OPENAI_API_KEY` from `.env`.
- [x] Use model `gpt-4.1-mini` per project requirement.
- [x] Add internal test route or test utility for basic connectivity check (`2+2`).
- [x] Add error handling for missing key and API failures.

### Tests

- [x] Unit tests with mocked OpenAI client.
- [x] Integration test path for configured key and expected response shape.
- [x] Negative integration test for missing/invalid API key behavior.

### Success criteria

- [x] Backend can successfully complete a simple OpenAI call.
- [x] Failure modes are understandable and non-destructive.

### Implemented design decisions

- [x] Connectivity check is exposed as authenticated `POST /api/ai/connectivity`.
- [x] Missing API key returns `503`; provider failure returns `502`.

## Part 9: Structured Outputs for chat + optional board updates

### Checklist

- [x] Finalize schema proposal with user sign-off before coding.
- [x] Send board JSON, user prompt, and conversation history to model.
- [x] Parse and validate structured response.
- [x] Apply optional board update atomically when included.
- [x] Return both assistant text and update result to caller.

### Proposed schema draft (for sign-off)

- [x] `assistant_message`: string
- [x] `board_update`: object or null
- [x] `board_update.operations`: array of operations
- [x] Operation types:
- [x] `create_card` with `column_id`, `title`, `details`
- [x] `edit_card` with `card_id`, optional `title`, optional `details`
- [x] `move_card` with `card_id`, `to_column_id`, optional `before_card_id`
- [x] `delete_card` with `card_id`
- [x] `rename_column` with `column_id`, `title`

### Tests

- [x] Unit tests for schema validation and operation application.
- [x] Integration tests for no-update and update-included responses.
- [x] Integration tests for invalid model outputs (safe reject path).
- [x] Review unit coverage pragmatically; prioritize valuable cases over strict quota.

### Success criteria

- [x] AI responses are reliably parsed and validated.
- [x] Valid updates are applied correctly; invalid updates are rejected safely.

## Part 10: Frontend AI sidebar and auto-refresh behavior

### Checklist

- [ ] Add sidebar chat UI integrated with backend AI endpoint.
- [ ] Display conversation history and request status.
- [ ] Apply backend-confirmed board updates and refresh board state.
- [ ] Keep interaction design clean and readable on desktop and mobile.

### Tests

- [ ] Component/unit tests for chat UI state transitions.
- [ ] Integration tests for chat request/response rendering.
- [ ] End-to-end test covering AI-triggered board mutation reflected in UI.
- [ ] Review unit coverage pragmatically; prioritize valuable cases over strict quota.

### Success criteria

- [ ] Sidebar chat is usable and stable.
- [ ] Board updates from AI appear automatically after response.
- [ ] No regression in existing Kanban interactions.

## Quality gates (applies to all implementation parts)

- [ ] Root cause first: identify and verify cause before fixing issues.
- [ ] Keep implementation simple and avoid over-engineering.
- [ ] Keep docs concise and updated as behavior changes.
- [ ] Keep testing pragmatic: prioritize high-value tests and use coverage targets only when sensible.
- [ ] Do not proceed to next part until current part meets success criteria.