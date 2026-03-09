# Kanban Studio

## Run

```bash
npm install
npm run dev
```

Frontend dev mode expects the FastAPI backend running on `http://localhost:8000`.
Next.js rewrites `/api/*`, `/auth/*`, and `/login` to that backend.
Set `BACKEND_ORIGIN` if your backend runs on a different origin.

## Tests

```bash
npm run test:unit
npm run test:e2e
```
