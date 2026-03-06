# Project Plan

## Working agreements

- [ ] Use Part 1 as a hard gate. No implementation for Part 2+ until user approval.
- [ ] Keep architecture to a single Docker container for the MVP.
- [ ] Keep auth/session simple for MVP.
- [ ] Target minimum 80% unit test coverage and robust integration testing across implemented parts.
- [ ] Propose AI Structured Output schema for user sign-off before implementation.
- [ ] Define script filenames and conventions in Part 2.

## Part 1: Planning and documentation gate

### Checklist

- [x] Expand this plan with detailed checklists.
- [x] Add tests and success criteria for each part.
- [x] Create `frontend/AGENTS.md` describing current frontend code.
- [x] User reviews and approves plan before Part 2 starts.

### Tests

- [ ] Documentation quality review against business requirements and technical decisions.
- [ ] Confirm each part has explicit deliverables, tests, and success criteria.

### Success criteria

- [ ] Plan is specific enough to execute without guesswork.
- [ ] Scope and ordering are clear and aligned with MVP constraints.
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

- [ ] Build Next.js frontend as static assets.
- [ ] Wire FastAPI to serve built frontend at `/`.
- [ ] Keep API namespace under `/api/*`.
- [ ] Ensure static asset paths resolve correctly in container.
- [ ] Remove temporary hello world route after frontend takeover.

### Tests

- [ ] Frontend unit tests pass with >=80% unit coverage threshold.
- [ ] Integration test: root route returns Kanban UI from backend server.
- [ ] Integration test: asset files load correctly (no broken JS/CSS references).
- [ ] Container smoke test: board visible at `/` after container startup.

### Success criteria

- [ ] Existing Kanban demo renders at `/` when run in container.
- [ ] API endpoints remain reachable under `/api`.
- [ ] Coverage gate is enforced and passing for unit tests.

## Part 4: Simple fake sign-in flow

### Checklist

- [ ] Add simple sign-in page/state with fixed credentials (`user` / `password`).
- [ ] Add simple session handling (cookie-based session acceptable for MVP).
- [ ] Gate Kanban route to signed-in users.
- [ ] Add logout action clearing session.
- [ ] Keep UX minimal and explicit for invalid credentials.

### Tests

- [ ] Unit tests for auth/session helpers and credential validation logic.
- [ ] Integration tests for login success/failure and route gating.
- [ ] Integration test for logout flow.
- [ ] Coverage check remains >=80% for unit tests.

### Success criteria

- [ ] Unauthenticated users cannot access board route.
- [ ] Correct credentials allow access and maintain session.
- [ ] Logout reliably returns user to signed-out state.

## Part 5: Database modeling and sign-off

### Checklist

- [ ] Propose SQLite schema for users and one board per user.
- [ ] Model board storage as JSON payload for columns/cards.
- [ ] Document schema, constraints, and migration approach in `docs/`.
- [ ] Propose AI output schema draft for later Part 9 sign-off.
- [ ] Obtain user sign-off before implementing data layer changes.

### Tests

- [ ] Validate schema proposal against required operations (read board, update board, card moves, edits).
- [ ] Confirm forward compatibility for multi-user support.

### Success criteria

- [ ] Data model is simple, documented, and sufficient for MVP use cases.
- [ ] User approves schema decisions before implementation.

## Part 6: Backend Kanban API with persistence

### Checklist

- [ ] Implement DB initialization on startup if DB file does not exist.
- [ ] Add API endpoints for reading and updating board data by user.
- [ ] Enforce simple auth/session checks on protected endpoints.
- [ ] Keep update contract explicit and validated.
- [ ] Add backend service/repository separation only as needed for clarity.

### Tests

- [ ] Backend unit tests for DB access and data transformation logic.
- [ ] API integration tests for success and error cases.
- [ ] Integration test for first-run DB creation path.
- [ ] Coverage check: backend unit tests >=80%.

### Success criteria

- [ ] Board state persists across restarts.
- [ ] API behavior is deterministic and documented.
- [ ] DB is auto-created without manual steps.

## Part 7: Connect frontend to backend API

### Checklist

- [ ] Replace frontend in-memory board state initialization with backend fetch.
- [ ] Persist board mutations through backend API.
- [ ] Handle loading and failure states with minimal UI feedback.
- [ ] Preserve drag/drop and card edit/create/delete behavior.

### Tests

- [ ] Frontend unit tests for API client and state transitions.
- [ ] Integration tests covering read-on-load and mutate-then-refresh flows.
- [ ] End-to-end test for persistence across page reload.
- [ ] Coverage check remains >=80% for unit tests.

### Success criteria

- [ ] UI reflects persisted backend state, not local demo-only state.
- [ ] Core Kanban interactions continue to work with API-backed data.

## Part 8: OpenAI connectivity validation

### Checklist

- [ ] Add backend OpenAI client wiring using `OPENAI_API_KEY` from `.env`.
- [ ] Use model `gpt-4.1-mini` per project requirement.
- [ ] Add internal test route or test utility for basic connectivity check (`2+2`).
- [ ] Add error handling for missing key and API failures.

### Tests

- [ ] Unit tests with mocked OpenAI client.
- [ ] Integration test path for configured key and expected response shape.
- [ ] Negative integration test for missing/invalid API key behavior.

### Success criteria

- [ ] Backend can successfully complete a simple OpenAI call.
- [ ] Failure modes are understandable and non-destructive.

## Part 9: Structured Outputs for chat + optional board updates

### Checklist

- [ ] Finalize schema proposal with user sign-off before coding.
- [ ] Send board JSON, user prompt, and conversation history to model.
- [ ] Parse and validate structured response.
- [ ] Apply optional board update atomically when included.
- [ ] Return both assistant text and update result to caller.

### Proposed schema draft (for sign-off)

- [ ] `assistant_message`: string
- [ ] `board_update`: object or null
- [ ] `board_update.operations`: array of operations
- [ ] Operation types:
- [ ] `create_card` with `column_id`, `title`, `details`
- [ ] `edit_card` with `card_id`, optional `title`, optional `details`
- [ ] `move_card` with `card_id`, `to_column_id`, optional `before_card_id`
- [ ] `delete_card` with `card_id`
- [ ] `rename_column` with `column_id`, `title`

### Tests

- [ ] Unit tests for schema validation and operation application.
- [ ] Integration tests for no-update and update-included responses.
- [ ] Integration tests for invalid model outputs (safe reject path).
- [ ] Coverage check: unit tests >=80%.

### Success criteria

- [ ] AI responses are reliably parsed and validated.
- [ ] Valid updates are applied correctly; invalid updates are rejected safely.

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
- [ ] Coverage check: unit tests >=80%.

### Success criteria

- [ ] Sidebar chat is usable and stable.
- [ ] Board updates from AI appear automatically after response.
- [ ] No regression in existing Kanban interactions.

## Quality gates (applies to all implementation parts)

- [ ] Root cause first: identify and verify cause before fixing issues.
- [ ] Keep implementation simple and avoid over-engineering.
- [ ] Keep docs concise and updated as behavior changes.
- [ ] Maintain >=80% unit test coverage with robust integration tests.
- [ ] Do not proceed to next part until current part meets success criteria.