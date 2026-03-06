# Data Model Proposal (Part 5)

## Scope

This document proposes the MVP persistence model and AI update schema for sign-off before implementation.

Goals:
- Simple SQLite schema
- One board per user for MVP
- Board stored as JSON for low-friction iteration
- Forward compatible with multi-user support

## SQLite Schema (Proposed)

Database file:
- `backend/data/app.db`

### Table: `users`

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_plaintext TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
```

Notes:
- For MVP, credentials remain fixed (`user` / `password`) and are seeded if missing.
- Password is intentionally plaintext for MVP simplicity only. A later hardening pass can switch to hashes.

### Table: `boards`

```sql
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  title TEXT NOT NULL DEFAULT 'Kanban Board',
  board_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Notes:
- `UNIQUE(user_id)` enforces one board per user (MVP requirement).
- `board_json` stores full board shape as serialized JSON.

### Suggested Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
```

## Board JSON Shape (Stored in `boards.board_json`)

This shape mirrors the existing frontend model (`columns`, `cards`).

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Task title",
      "details": "Task details"
    }
  }
}
```

## Initialization and Migration Approach

At backend startup (Part 6):
1. Ensure `backend/data/` exists.
2. Open/create `backend/data/app.db`.
3. Execute `CREATE TABLE IF NOT EXISTS` and index statements.
4. Seed MVP user `user` / `password` if not present.
5. Seed that user's board from current frontend initial board if no board exists.

Migration strategy for MVP:
- Keep a lightweight integer `schema_version` using SQLite `PRAGMA user_version`.
- Version `1` corresponds to the schema above.
- Use explicit SQL migration scripts when schema changes later.

## API Contract Implications (Part 6)

Expected operations supported by this model:
- Read board for authenticated user.
- Overwrite board JSON for authenticated user after validation.

This keeps backend logic simple while preserving all current frontend interactions.

## Validation Against Requirements

### Required operations

- Read board: supported by `SELECT board_json FROM boards WHERE user_id = ?`.
- Update board: supported by `UPDATE boards SET board_json = ?, updated_at = ... WHERE user_id = ?`.
- Card move/edit/create/delete: represented in JSON payload and persisted as one update.

### Multi-user forward compatibility

- `users` table supports multiple users.
- `boards.user_id` foreign key isolates board state per user.
- `UNIQUE(user_id)` can be relaxed later to support multiple boards per user if needed.

## AI Structured Output Proposal (For Part 9 Sign-off)

Model: `gpt-4.1-mini`

Response envelope:

```json
{
  "assistant_message": "string",
  "board_update": {
    "operations": [
      {
        "type": "create_card",
        "column_id": "col-backlog",
        "title": "New card",
        "details": "Optional details"
      }
    ]
  }
}
```

`board_update` may be `null` when no board change is needed.

### Allowed operation types

1. `create_card`
- Required: `column_id`, `title`, `details`

2. `edit_card`
- Required: `card_id`
- Optional: `title`, `details`
- At least one optional field must be present.

3. `move_card`
- Required: `card_id`, `to_column_id`
- Optional: `before_card_id` (insert before this card, else append)

4. `delete_card`
- Required: `card_id`

5. `rename_column`
- Required: `column_id`, `title`

### Backend validation rules

- Reject unknown operation types.
- Reject references to missing `card_id` or `column_id`.
- Apply operations in array order.
- If any operation is invalid, reject the full update (atomic failure).
- Preserve `assistant_message` even if update is rejected.

## Open Questions For Sign-off

1. Is plaintext password storage acceptable for MVP with planned later hardening?
- Approved: Yes.
2. Do you want `board_json` overwrite-only updates in Part 6, or should we design partial patch endpoints immediately?
- Approved: Overwrite-only updates for MVP.
3. Is atomic all-or-nothing validation for AI operations acceptable as default behavior?
- Approved: Yes.
