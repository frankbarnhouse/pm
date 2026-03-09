"use client";

import { FormEvent, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { AddColumnButton } from "@/components/AddColumnButton";
import { createId, initialData, moveCard, type BoardData, type CardLabel } from "@/lib/kanban";

type KanbanBoardProps = {
  boardId: number;
  onBack: () => void;
};

export const KanbanBoard = ({ boardId, onBack }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [boardTitle, setBoardTitle] = useState("Board");
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterPriority, setFilterPriority] = useState<string>("");
  const [filterLabel, setFilterLabel] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatStatus, setChatStatus] = useState<string | null>(null);
  const [isChatSending, setIsChatSending] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatDesktopHeight, setChatDesktopHeight] = useState(520);
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([
    {
      role: "assistant",
      content: "Ask me to create, edit, move, or delete cards. I can also rename columns.",
    },
  ]);
  const syncStatusTimerRef = useRef<number | null>(null);
  const chatStatusTimerRef = useRef<number | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const isResizingChatRef = useRef(false);
  const resizeStartYRef = useRef(0);
  const resizeStartHeightRef = useRef(520);
  const persistTimerRef = useRef<number | null>(null);
  const skipNextPersistRef = useRef(true);

  const showTransientSyncStatus = (message: string) => {
    setSyncStatus(message);
    if (syncStatusTimerRef.current) {
      window.clearTimeout(syncStatusTimerRef.current);
    }
    syncStatusTimerRef.current = window.setTimeout(() => {
      setSyncStatus(null);
      syncStatusTimerRef.current = null;
    }, 2200);
  };

  useEffect(() => {
    let cancelled = false;

    const loadBoard = async () => {
      try {
        const response = await fetch(`/api/boards/${boardId}`);
        if (response.status === 401) {
          window.location.assign("/login");
          return;
        }
        if (!response.ok) {
          throw new Error(`Failed to load board: ${response.status}`);
        }

        const payload = (await response.json()) as { board?: BoardData; title?: string };
        if (!payload.board) {
          throw new Error("Board payload missing");
        }

        if (!cancelled) {
          setBoard(payload.board);
          if (payload.title) {
            setBoardTitle(payload.title);
          }
        }
      } catch {
        if (!cancelled) {
          setSyncStatus("Using local board. Changes may not persist.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadBoard();

    return () => {
      cancelled = true;
      if (syncStatusTimerRef.current) {
        window.clearTimeout(syncStatusTimerRef.current);
      }
      if (chatStatusTimerRef.current) {
        window.clearTimeout(chatStatusTimerRef.current);
      }
      if (persistTimerRef.current) {
        window.clearTimeout(persistTimerRef.current);
      }
    };
  }, [boardId]);

  useEffect(() => {
    if (skipNextPersistRef.current) {
      skipNextPersistRef.current = false;
      return;
    }
    if (persistTimerRef.current) {
      window.clearTimeout(persistTimerRef.current);
    }
    persistTimerRef.current = window.setTimeout(() => {
      persistTimerRef.current = null;
      void persistBoard(board);
    }, 500);
    return () => {
      if (persistTimerRef.current) {
        window.clearTimeout(persistTimerRef.current);
      }
    };
  }, [board]);

  useEffect(() => {
    if (!isChatOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsChatOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isChatOpen]);

  useEffect(() => {
    if (!chatScrollRef.current) {
      return;
    }
    chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
  }, [chatMessages]);

  useEffect(() => {
    const onPointerMove = (event: PointerEvent) => {
      if (!isResizingChatRef.current) {
        return;
      }

      const delta = resizeStartYRef.current - event.clientY;
      const minHeight = 520;
      const maxHeight = Math.max(minHeight, window.innerHeight - 48);
      const nextHeight = Math.min(
        maxHeight,
        Math.max(minHeight, resizeStartHeightRef.current + delta)
      );
      setChatDesktopHeight(nextHeight);
    };

    const onPointerUp = () => {
      isResizingChatRef.current = false;
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };
  }, []);

  const startChatResize = (event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    isResizingChatRef.current = true;
    resizeStartYRef.current = event.clientY;
    resizeStartHeightRef.current = chatDesktopHeight;
  };

  const persistBoard = async (nextBoard: BoardData) => {
    try {
      const response = await fetch(`/api/boards/${boardId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(nextBoard),
      });

      if (response.status === 401) {
        window.location.assign("/login");
        return;
      }
      if (!response.ok) {
        throw new Error(`Failed to save board: ${response.status}`);
      }

      showTransientSyncStatus("Saved");
    } catch {
      setSyncStatus("Unable to save right now.");
    }
  };

  const loadBoardForRefresh = async (): Promise<BoardData | null> => {
    const response = await fetch(`/api/boards/${boardId}`);
    if (response.status === 401) {
      window.location.assign("/login");
      return null;
    }
    if (!response.ok) {
      throw new Error(`Failed to refresh board: ${response.status}`);
    }

    const payload = (await response.json()) as { board?: BoardData };
    if (!payload.board) {
      throw new Error("Board payload missing");
    }
    return payload.board;
  };

  const showTransientChatStatus = (message: string) => {
    setChatStatus(message);
    if (chatStatusTimerRef.current) {
      window.clearTimeout(chatStatusTimerRef.current);
    }
    chatStatusTimerRef.current = window.setTimeout(() => {
      setChatStatus(null);
      chatStatusTimerRef.current = null;
    }, 2600);
  };

  const handleChatSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const prompt = chatInput.trim();
    if (!prompt || isChatSending) {
      return;
    }

    setIsChatSending(true);
    setChatInput("");
    setChatMessages((previous) => [...previous, { role: "user", content: prompt }]);
    setChatStatus("Thinking...");

    try {
      const response = await fetch(`/api/boards/${boardId}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      if (response.status === 401) {
        window.location.assign("/login");
        return;
      }
      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.status}`);
      }

      const payload = (await response.json()) as {
        assistant_message?: string;
        board_updated?: boolean;
      };
      const assistantMessage = payload.assistant_message?.trim();
      if (!assistantMessage) {
        throw new Error("Missing assistant_message");
      }

      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", content: assistantMessage },
      ]);

      if (payload.board_updated) {
        try {
          const refreshed = await loadBoardForRefresh();
          if (refreshed) {
            skipNextPersistRef.current = true;
            setBoard(refreshed);
          }
          showTransientChatStatus("Applied update and refreshed board.");
        } catch {
          showTransientChatStatus("Update applied but refresh failed. Reload the page.");
        }
      } else {
        showTransientChatStatus("Reply received.");
      }
    } catch {
      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: "I could not complete that request right now. Please try again.",
        },
      ]);
      setChatStatus("Unable to send message.");
    } finally {
      setIsChatSending(false);
    }
  };

  const updateBoard = (updater: (previous: BoardData) => BoardData) => {
    setBoard(updater);
  };

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    updateBoard((previous) => ({
      ...previous,
      columns: moveCard(previous.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    updateBoard((previous) => ({
      ...previous,
      columns: previous.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    updateBoard((previous) => ({
      ...previous,
      cards: {
        ...previous.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: previous.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    updateBoard((previous) => {
      return {
        ...previous,
        cards: Object.fromEntries(
          Object.entries(previous.cards).filter(([id]) => id !== cardId)
        ),
        columns: previous.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const handleUpdateCard = (cardId: string, updates: { title?: string; details?: string; priority?: "low" | "medium" | "high" | null; due_date?: string | null; labels?: CardLabel[] }) => {
    updateBoard((previous) => ({
      ...previous,
      cards: {
        ...previous.cards,
        [cardId]: { ...previous.cards[cardId], ...updates },
      },
    }));
  };

  const handleAddColumn = (title: string) => {
    const id = createId("col");
    updateBoard((previous) => ({
      ...previous,
      columns: [...previous.columns, { id, title, cardIds: [] }],
    }));
  };

  const handleDeleteColumn = (columnId: string) => {
    updateBoard((previous) => ({
      ...previous,
      cards: Object.fromEntries(
        Object.entries(previous.cards).filter(([cardId]) => {
          const column = previous.columns.find((c) => c.id === columnId);
          return !column?.cardIds.includes(cardId);
        })
      ),
      columns: previous.columns.filter((c) => c.id !== columnId),
    }));
  };

  const activeCard = activeCardId ? board.cards[activeCardId] : null;

  const hasFilter = searchQuery.trim() !== "" || filterPriority !== "" || filterLabel !== "";

  const matchesFilter = (card: { title: string; details: string; priority?: string | null; labels?: string[] }) => {
    if (!hasFilter) return true;
    const query = searchQuery.toLowerCase();
    const textMatch =
      !query ||
      card.title.toLowerCase().includes(query) ||
      card.details.toLowerCase().includes(query);
    const priorityMatch = !filterPriority || card.priority === filterPriority;
    const labelMatch = !filterLabel || (card.labels || []).includes(filterLabel);
    return textMatch && priorityMatch && labelMatch;
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1800px] flex-col gap-6 px-4 pb-12 pt-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--stroke)] bg-white/80 px-6 py-4 shadow-[0_4px_16px_rgba(3,33,71,0.06)] backdrop-blur">
          <div className="flex items-center gap-5">
            <button
              type="button"
              onClick={onBack}
              className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
              aria-label="Back to boards"
              data-testid="back-to-boards"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
            <div>
              <h1 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
                {boardTitle}
              </h1>
              <p className="text-xs text-[var(--gray-text)]">
                Drag cards between columns to track progress
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {syncStatus && (
              <span className="text-xs font-medium text-[var(--gray-text)]">
                {syncStatus}
              </span>
            )}
            {isLoading && (
              <span className="text-xs font-medium text-[var(--gray-text)]">
                Loading...
              </span>
            )}
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

        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[var(--stroke)] bg-white/80 px-4 py-2.5 shadow-[0_2px_8px_rgba(3,33,71,0.04)] backdrop-blur">
          <div className="relative flex-1 min-w-[180px]">
            <svg className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--gray-text)]" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              placeholder="Search cards..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-[var(--stroke)] bg-[var(--surface)] py-1.5 pl-8 pr-3 text-xs text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              data-testid="card-search"
            />
          </div>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-2 py-1.5 text-xs text-[var(--navy-dark)] outline-none"
            data-testid="priority-filter"
          >
            <option value="">All priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={filterLabel}
            onChange={(e) => setFilterLabel(e.target.value)}
            className="rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-2 py-1.5 text-xs text-[var(--navy-dark)] outline-none"
            data-testid="label-filter"
          >
            <option value="">All labels</option>
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
            <option value="improvement">Improvement</option>
            <option value="documentation">Docs</option>
            <option value="urgent">Urgent</option>
            <option value="design">Design</option>
            <option value="research">Research</option>
          </select>
          {hasFilter && (
            <button
              type="button"
              onClick={() => { setSearchQuery(""); setFilterPriority(""); setFilterLabel(""); }}
              className="rounded-lg border border-[var(--stroke)] px-2.5 py-1.5 text-xs font-medium text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
              data-testid="clear-filters"
            >
              Clear
            </button>
          )}
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="flex gap-4 overflow-x-auto pb-2">
            {board.columns.map((column, index) => (
              <div key={column.id} className="w-[300px] flex-shrink-0 lg:w-auto lg:flex-1">
                <KanbanColumn
                  column={column}
                  columnIndex={index}
                  cards={column.cardIds.map((cardId) => board.cards[cardId]).filter(Boolean).filter(matchesFilter)}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                  onUpdateCard={handleUpdateCard}
                  onDeleteColumn={board.columns.length > 1 ? handleDeleteColumn : undefined}
                />
              </div>
            ))}
            <div className="flex w-[300px] flex-shrink-0 items-start lg:w-auto lg:flex-1">
              <AddColumnButton onAdd={handleAddColumn} />
            </div>
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>

      <button
        type="button"
        aria-label="Open board chat"
        data-testid="chat-launcher"
        onClick={() => setIsChatOpen(true)}
        className="fixed bottom-6 right-6 z-40 inline-flex h-14 w-14 items-center justify-center rounded-full border border-[var(--stroke)] bg-[var(--secondary-purple)] text-white shadow-[var(--shadow)] transition hover:bg-[#5f2f77]"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 5.5C4 4.67 4.67 4 5.5 4H18.5C19.33 4 20 4.67 20 5.5V14.5C20 15.33 19.33 16 18.5 16H10.5L6 20V16H5.5C4.67 16 4 15.33 4 14.5V5.5Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {isChatOpen && (
        <button
          type="button"
          aria-label="Close board chat"
          className="fixed inset-0 z-40 bg-[rgba(3,33,71,0.28)]"
          onClick={() => setIsChatOpen(false)}
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-screen flex-col border-[var(--stroke)] bg-white p-5 shadow-[var(--shadow)] transition duration-300 sm:bottom-6 sm:right-6 sm:left-auto sm:top-auto sm:h-[var(--chat-desktop-height)] sm:w-[360px] sm:rounded-[28px] sm:border ${
          isChatOpen
            ? "translate-y-0 opacity-100"
            : "pointer-events-none translate-y-6 opacity-0"
        }`}
        style={{ ["--chat-desktop-height" as string]: `${chatDesktopHeight}px` }}
        data-testid="ai-chat-drawer"
        aria-hidden={!isChatOpen}
      >
        <button
          type="button"
          aria-label="Resize board chat"
          onPointerDown={startChatResize}
          className="-mx-1 mb-3 hidden cursor-ns-resize items-center justify-center rounded-full py-1 sm:flex"
        >
          <span className="h-1 w-14 rounded-full bg-[var(--stroke)]" />
        </button>
        <div className="flex items-start justify-between gap-4 border-b border-[var(--stroke)] pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
              AI Assistant
            </p>
            <h2 className="mt-2 font-display text-2xl text-[var(--navy-dark)]">Board Chat</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
              Ask for planning help or direct board changes. Applied updates refresh automatically.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close board chat"
            onClick={() => setIsChatOpen(false)}
            className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div
          ref={chatScrollRef}
          className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1"
          aria-live="polite"
        >
          {chatMessages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={
                message.role === "assistant"
                  ? "rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm leading-6 text-[var(--navy-dark)]"
                  : "rounded-2xl border border-transparent bg-[var(--primary-blue)] px-4 py-3 text-sm leading-6 text-white"
              }
            >
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.2em] opacity-75">
                {message.role === "assistant" ? "Assistant" : "You"}
              </p>
              <p>{message.content}</p>
            </div>
          ))}
        </div>

        <form onSubmit={handleChatSubmit} className="mt-4 space-y-3 border-t border-[var(--stroke)] pt-4">
          <label htmlFor="chat-prompt" className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Message
          </label>
          <textarea
            id="chat-prompt"
            value={chatInput}
            onChange={(event) => setChatInput(event.target.value)}
            rows={3}
            placeholder="Try: Move card-3 to In Progress and rename Review to QA"
            className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm leading-6 text-[var(--navy-dark)] outline-none transition focus:border-[var(--secondary-purple)]"
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--gray-text)]">
              {chatStatus || "Ready"}
            </p>
            <button
              type="submit"
              disabled={!chatInput.trim() || isChatSending}
              className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-[#5f2f77] disabled:cursor-not-allowed disabled:opacity-55"
            >
              {isChatSending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>
      </aside>
    </div>
  );
};
