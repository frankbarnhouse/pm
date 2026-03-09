"use client";

import { FormEvent, useEffect, useState } from "react";
import type { BoardMeta } from "@/lib/kanban";

type BoardDashboardProps = {
  onSelectBoard: (boardId: number) => void;
};

export const BoardDashboard = ({ onSelectBoard }: BoardDashboardProps) => {
  const [boards, setBoards] = useState<BoardMeta[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const loadBoards = async () => {
    try {
      const response = await fetch("/api/boards");
      if (response.status === 401) {
        window.location.assign("/login");
        return;
      }
      if (!response.ok) {
        throw new Error("Failed to load boards");
      }
      const payload = (await response.json()) as { boards: BoardMeta[] };
      setBoards(payload.boards);
    } catch {
      // Silently fail
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadBoards();
  }, []);

  const handleCreateBoard = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const response = await fetch("/api/boards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle.trim(),
          description: newDescription.trim(),
        }),
      });
      if (response.status === 401) {
        window.location.assign("/login");
        return;
      }
      if (!response.ok) {
        throw new Error("Failed to create board");
      }
      setNewTitle("");
      setNewDescription("");
      setIsCreating(false);
      await loadBoards();
    } catch {
      // Silently fail
    }
  };

  const handleDuplicateBoard = async (boardId: number) => {
    try {
      const response = await fetch(`/api/boards/${boardId}/duplicate`, {
        method: "POST",
      });
      if (response.ok) {
        await loadBoards();
      }
    } catch {
      // Silently fail
    }
  };

  const handleDeleteBoard = async (boardId: number) => {
    try {
      const response = await fetch(`/api/boards/${boardId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadBoards();
      }
    } catch {
      // Silently fail
    }
  };

  const handleUpdateBoard = async (boardId: number) => {
    try {
      const response = await fetch(`/api/boards/${boardId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: editTitle.trim(),
          description: editDescription.trim(),
        }),
      });
      if (response.ok) {
        setEditingId(null);
        await loadBoards();
      }
    } catch {
      // Silently fail
    }
  };

  const startEditing = (board: BoardMeta) => {
    setEditingId(board.id);
    setEditTitle(board.title);
    setEditDescription(board.description);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1000px] flex-col gap-6 px-4 pb-12 pt-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--stroke)] bg-white/80 px-6 py-4 shadow-[0_4px_16px_rgba(3,33,71,0.06)] backdrop-blur">
          <div>
            <h1 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
              Kanban Studio
            </h1>
            <p className="text-xs text-[var(--gray-text)]">
              Select a board or create a new one
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsCreating(true)}
              className="inline-flex items-center gap-1.5 rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
              data-testid="create-board-btn"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New board
            </button>
            <form action="/auth/logout" method="post">
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--stroke)] px-3 py-1.5 text-xs font-medium text-[var(--gray-text)] transition hover:border-[var(--secondary-purple)] hover:text-[var(--secondary-purple)]"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Log out
              </button>
            </form>
          </div>
        </header>

        {isCreating && (
          <div className="rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[0_4px_16px_rgba(3,33,71,0.06)]">
            <h2 className="mb-4 font-display text-lg font-semibold text-[var(--navy-dark)]">
              Create a new board
            </h2>
            <form onSubmit={handleCreateBoard} className="space-y-4">
              <div>
                <label htmlFor="board-title" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
                  Board title
                </label>
                <input
                  id="board-title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Sprint 42"
                  required
                  className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                />
              </div>
              <div>
                <label htmlFor="board-description" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
                  Description (optional)
                </label>
                <textarea
                  id="board-description"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="What is this board for?"
                  rows={2}
                  className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)]"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => { setIsCreating(false); setNewTitle(""); setNewDescription(""); }}
                  className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <span className="text-sm font-medium text-[var(--gray-text)]">Loading boards...</span>
          </div>
        ) : boards.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-[var(--stroke)] py-20">
            <p className="text-sm text-[var(--gray-text)]">No boards yet. Create your first one.</p>
            <button
              type="button"
              onClick={() => setIsCreating(true)}
              className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
            >
              Create board
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="board-list">
            {boards.map((board) => (
              <div
                key={board.id}
                className="group relative flex flex-col rounded-2xl border border-[var(--stroke)] bg-white p-5 shadow-[0_4px_12px_rgba(3,33,71,0.06)] transition-all hover:shadow-[0_8px_20px_rgba(3,33,71,0.10)]"
                data-testid={`board-card-${board.id}`}
              >
                {editingId === board.id ? (
                  <div className="space-y-3">
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full rounded-lg border border-[var(--stroke)] px-2 py-1 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                    />
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      rows={2}
                      className="w-full resize-none rounded-lg border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)]"
                    />
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleUpdateBoard(board.id)}
                        className="rounded-full bg-[var(--primary-blue)] px-3 py-1 text-[10px] font-semibold uppercase text-white"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="rounded-full border border-[var(--stroke)] px-3 py-1 text-[10px] font-semibold uppercase text-[var(--gray-text)]"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => onSelectBoard(board.id)}
                      className="flex-1 text-left"
                      data-testid={`open-board-${board.id}`}
                    >
                      <h3 className="font-display text-base font-semibold text-[var(--navy-dark)]">
                        {board.title}
                      </h3>
                      {board.description && (
                        <p className="mt-1 text-xs leading-5 text-[var(--gray-text)]">
                          {board.description}
                        </p>
                      )}
                      <div className="mt-3 flex items-center gap-3 text-[10px] font-medium text-[var(--gray-text)]">
                        {board.card_count !== undefined && (
                          <span>{board.card_count} {board.card_count === 1 ? "card" : "cards"}</span>
                        )}
                        {board.column_count !== undefined && (
                          <span>{board.column_count} {board.column_count === 1 ? "column" : "columns"}</span>
                        )}
                        <span>Updated {formatDate(board.updated_at)}</span>
                      </div>
                    </button>
                    <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); startEditing(board); }}
                        className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--primary-blue)]"
                        aria-label={`Edit ${board.title}`}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleDuplicateBoard(board.id); }}
                        className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--secondary-purple)]"
                        aria-label={`Duplicate ${board.title}`}
                        data-testid={`duplicate-board-${board.id}`}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleDeleteBoard(board.id); }}
                        className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-red-50 hover:text-red-500"
                        aria-label={`Delete ${board.title}`}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M3 6h18" />
                          <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                        </svg>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
