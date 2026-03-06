# Frontend Agent Notes

## Purpose

This directory contains the existing frontend-only MVP demo for the Kanban UI.
It is built with Next.js App Router and currently runs without backend persistence.

## Current stack

- Next.js 16 (`frontend/package.json`)
- React 19
- TypeScript (strict mode)
- Tailwind CSS v4 via `@import "tailwindcss"`
- Drag and drop via `@dnd-kit/core` and `@dnd-kit/sortable`
- Unit tests with Vitest + Testing Library
- End-to-end tests with Playwright

## App entry points

- `src/app/layout.tsx`: Global layout, metadata, and Google fonts (`Space Grotesk`, `Manrope`)
- `src/app/page.tsx`: Renders `KanbanBoard`
- `src/app/globals.css`: Global theme tokens and base styles

## Kanban architecture

- `src/components/KanbanBoard.tsx`
- Owns board state in component-local React state (`useState`)
- Starts from `initialData` in `src/lib/kanban.ts`
- Handles drag lifecycle via `DndContext`
- Supports:
- Renaming columns
- Adding cards
- Deleting cards
- Dragging cards within and across columns
- No backend calls yet; all data is in-memory

- `src/components/KanbanColumn.tsx`
- Renders a single column with editable title input
- Uses `useDroppable` and `SortableContext`
- Hosts `NewCardForm`

- `src/components/KanbanCard.tsx`
- Sortable draggable card with remove button

- `src/components/KanbanCardPreview.tsx`
- Drag overlay card preview

- `src/components/NewCardForm.tsx`
- Inline add-card form with local open/close and form state

## Domain/state helpers

- `src/lib/kanban.ts`
- Defines core types: `Card`, `Column`, `BoardData`
- Contains seeded `initialData` with five columns
- Includes pure helper `moveCard(columns, activeId, overId)`
- Includes `createId(prefix)` for new card IDs

## Testing setup

- Unit/component tests:
- `src/components/KanbanBoard.test.tsx`
- `src/lib/kanban.test.ts`
- Config:
- `vitest.config.ts` (jsdom, coverage reporters text/html)
- `src/test/setup.ts` (`@testing-library/jest-dom`)

- E2E tests:
- `tests/kanban.spec.ts`
- Config:
- `playwright.config.ts` (starts dev server on `127.0.0.1:3000`)

## Scripts

- `npm run dev`: Next.js dev server
- `npm run build`: Next.js production build
- `npm run start`: Next.js production server
- `npm run test:unit`: Run unit tests
- `npm run test:e2e`: Run Playwright tests
- `npm run test:all`: Unit + e2e

## Current constraints

- Frontend is a standalone demo and not yet integrated with FastAPI.
- Auth is not implemented in frontend yet.
- Board persistence is not implemented; state resets on reload.
- AI chat sidebar is not implemented yet.

## Guidance for future changes

- Keep UI behavior parity while migrating to backend-backed data.
- Prefer pure helper logic for board operations to keep tests simple.
- Preserve stable test IDs used by unit/e2e tests (`column-*`, `card-*`).
- Keep route structure simple: board remains rooted at `/` unless project plan changes.
