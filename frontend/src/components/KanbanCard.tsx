import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

const priorityStyles: Record<string, { dot: string; label: string }> = {
  high: { dot: "bg-red-500", label: "High" },
  medium: { dot: "bg-[var(--accent-yellow)]", label: "Medium" },
  low: { dot: "bg-[#34a77f]", label: "Low" },
};

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onUpdateCard?: (cardId: string, updates: { priority?: "low" | "medium" | "high" | null; due_date?: string | null }) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdateCard }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const { ["aria-describedby"]: _ariaDescribedBy, ...sortableAttributes } = attributes;
  const [showDetails, setShowDetails] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const priority = card.priority ? priorityStyles[card.priority] : null;

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr + "T00:00:00");
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  };

  const isDueSoon = (dateStr: string) => {
    const due = new Date(dateStr + "T23:59:59");
    const now = new Date();
    const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return diffDays < 0 ? "overdue" : diffDays <= 2 ? "soon" : "ok";
  };

  return (
    <>
      <article
        ref={setNodeRef}
        style={style}
        className={clsx(
          "group relative rounded-2xl border border-transparent bg-white px-4 py-3 shadow-[0_4px_12px_rgba(3,33,71,0.06)]",
          "transition-all duration-150",
          "hover:shadow-[0_8px_20px_rgba(3,33,71,0.10)]",
          isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
        )}
        {...sortableAttributes}
        {...listeners}
        data-testid={`card-${card.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {priority && (
                <span className={clsx("h-2 w-2 flex-shrink-0 rounded-full", priority.dot)} title={`${priority.label} priority`} />
              )}
              <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
                {card.title}
              </h4>
            </div>
            {card.details && (
              <p className="mt-1 text-xs leading-5 text-[var(--gray-text)]">
                {card.details}
              </p>
            )}
            <div className="mt-2 flex items-center gap-2">
              {card.due_date && (
                <span
                  className={clsx(
                    "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                    isDueSoon(card.due_date) === "overdue" && "bg-red-50 text-red-600",
                    isDueSoon(card.due_date) === "soon" && "bg-amber-50 text-amber-600",
                    isDueSoon(card.due_date) === "ok" && "bg-[var(--surface)] text-[var(--gray-text)]"
                  )}
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  {formatDueDate(card.due_date)}
                </span>
              )}
              {priority && (
                <span className="rounded-md bg-[var(--surface)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--gray-text)]">
                  {priority.label}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-shrink-0 gap-0.5 opacity-0 transition group-hover:opacity-100">
            {onUpdateCard && (
              <button
                type="button"
                onClick={() => setShowDetails(true)}
                className="rounded-lg p-1 text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--primary-blue)]"
                aria-label={`Edit details for ${card.title}`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
            )}
            <button
              type="button"
              onClick={() => onDelete(card.id)}
              className="rounded-lg p-1 text-[var(--gray-text)] hover:bg-red-50 hover:text-red-500"
              aria-label={`Delete ${card.title}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M3 6h18" />
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          </div>
        </div>
      </article>

      {showDetails && onUpdateCard && (
        <CardDetailsModal
          card={card}
          onClose={() => setShowDetails(false)}
          onUpdate={(updates) => {
            onUpdateCard(card.id, updates);
            setShowDetails(false);
          }}
        />
      )}
    </>
  );
};

type CardDetailsModalProps = {
  card: Card;
  onClose: () => void;
  onUpdate: (updates: { priority?: "low" | "medium" | "high" | null; due_date?: string | null }) => void;
};

const CardDetailsModal = ({ card, onClose, onUpdate }: CardDetailsModalProps) => {
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "">(card.priority || "");
  const [dueDate, setDueDate] = useState(card.due_date || "");

  const handleSave = () => {
    onUpdate({
      priority: priority || null,
      due_date: dueDate || null,
    });
  };

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-50 bg-[rgba(3,33,71,0.28)]"
        onClick={onClose}
        aria-label="Close card details"
      />
      <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[0_18px_40px_rgba(3,33,71,0.16)]" data-testid="card-details-modal">
        <h3 className="mb-4 font-display text-lg font-semibold text-[var(--navy-dark)]">
          {card.title}
        </h3>
        {card.details && (
          <p className="mb-4 text-sm leading-6 text-[var(--gray-text)]">{card.details}</p>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="card-priority" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Priority
            </label>
            <select
              id="card-priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as "low" | "medium" | "high" | "")}
              className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none"
            >
              <option value="">None</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div>
            <label htmlFor="card-due-date" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Due date
            </label>
            <input
              id="card-due-date"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none"
            />
          </div>
        </div>

        <div className="mt-5 flex gap-3">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
          >
            Save
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          >
            Cancel
          </button>
        </div>
      </div>
    </>
  );
};
