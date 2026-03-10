import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card, CardLabel, CardComment, ChecklistItem } from "@/lib/kanban";
import { LABEL_COLORS } from "@/lib/kanban";

const priorityStyles: Record<string, { dot: string; label: string }> = {
  high: { dot: "bg-red-500", label: "High" },
  medium: { dot: "bg-[var(--accent-yellow)]", label: "Medium" },
  low: { dot: "bg-[#34a77f]", label: "Low" },
};

const ALL_LABELS: CardLabel[] = ["bug", "feature", "improvement", "documentation", "urgent", "design", "research"];

type CardUpdates = {
  title?: string;
  details?: string;
  priority?: "low" | "medium" | "high" | null;
  due_date?: string | null;
  labels?: CardLabel[];
};

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onUpdateCard?: (cardId: string, updates: CardUpdates) => void;
  onAddComment?: (cardId: string, text: string) => void;
  onDeleteComment?: (cardId: string, commentId: string) => void;
  onAddChecklistItem?: (cardId: string, text: string) => void;
  onToggleChecklistItem?: (cardId: string, itemId: string) => void;
  onDeleteChecklistItem?: (cardId: string, itemId: string) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdateCard, onAddComment, onDeleteComment, onAddChecklistItem, onToggleChecklistItem, onDeleteChecklistItem }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const { ["aria-describedby"]: _ariaDescribedBy, ...sortableAttributes } = attributes;
  const [showDetails, setShowDetails] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const priority = card.priority ? priorityStyles[card.priority] : null;
  const cardLabels = card.labels || [];
  const commentCount = card.comments?.length || 0;
  const checklistItems = card.checklist || [];
  const checklistTotal = checklistItems.length;
  const checklistDone = checklistItems.filter((i) => i.done).length;

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr + "T00:00:00");
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  };

  const getDueStatus = (dateStr: string): "overdue" | "soon" | "ok" => {
    const due = new Date(dateStr + "T23:59:59");
    const diffDays = (due.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    if (diffDays < 0) return "overdue";
    if (diffDays <= 2) return "soon";
    return "ok";
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
        {cardLabels.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1">
            {cardLabels.map((label) => {
              const style = LABEL_COLORS[label];
              return style ? (
                <span
                  key={label}
                  className={clsx("rounded-md px-1.5 py-0.5 text-[10px] font-semibold", style.bg, style.text)}
                  data-testid={`label-${label}`}
                >
                  {style.name}
                </span>
              ) : null;
            })}
          </div>
        )}
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
                    getDueStatus(card.due_date) === "overdue" && "bg-red-50 text-red-600",
                    getDueStatus(card.due_date) === "soon" && "bg-amber-50 text-amber-600",
                    getDueStatus(card.due_date) === "ok" && "bg-[var(--surface)] text-[var(--gray-text)]"
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
              {commentCount > 0 && (
                <span className="inline-flex items-center gap-0.5 rounded-md bg-[var(--surface)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--gray-text)]" data-testid="comment-count">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  {commentCount}
                </span>
              )}
              {checklistTotal > 0 && (
                <span
                  className={clsx(
                    "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                    checklistDone === checklistTotal
                      ? "bg-green-50 text-green-600"
                      : "bg-[var(--surface)] text-[var(--gray-text)]"
                  )}
                  data-testid="checklist-progress"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <polyline points="9 11 12 14 22 4" />
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                  </svg>
                  {checklistDone}/{checklistTotal}
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
          onAddComment={onAddComment ? (text) => onAddComment(card.id, text) : undefined}
          onDeleteComment={onDeleteComment ? (commentId) => onDeleteComment(card.id, commentId) : undefined}
          onAddChecklistItem={onAddChecklistItem ? (text) => onAddChecklistItem(card.id, text) : undefined}
          onToggleChecklistItem={onToggleChecklistItem ? (itemId) => onToggleChecklistItem(card.id, itemId) : undefined}
          onDeleteChecklistItem={onDeleteChecklistItem ? (itemId) => onDeleteChecklistItem(card.id, itemId) : undefined}
        />
      )}
    </>
  );
};

type CardDetailsModalProps = {
  card: Card;
  onClose: () => void;
  onUpdate: (updates: CardUpdates) => void;
  onAddComment?: (text: string) => void;
  onDeleteComment?: (commentId: string) => void;
  onAddChecklistItem?: (text: string) => void;
  onToggleChecklistItem?: (itemId: string) => void;
  onDeleteChecklistItem?: (itemId: string) => void;
};

const CardDetailsModal = ({ card, onClose, onUpdate, onAddComment, onDeleteComment, onAddChecklistItem, onToggleChecklistItem, onDeleteChecklistItem }: CardDetailsModalProps) => {
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "">(card.priority || "");
  const [dueDate, setDueDate] = useState(card.due_date || "");
  const [selectedLabels, setSelectedLabels] = useState<Set<CardLabel>>(
    new Set(card.labels || [])
  );
  const [newComment, setNewComment] = useState("");
  const [newChecklistText, setNewChecklistText] = useState("");

  const toggleLabel = (label: CardLabel) => {
    setSelectedLabels((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const handleSave = () => {
    onUpdate({
      title: title.trim() || card.title,
      details: details.trim(),
      priority: priority || null,
      due_date: dueDate || null,
      labels: Array.from(selectedLabels),
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
      <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[0_18px_40px_rgba(3,33,71,0.16)] max-h-[90vh] overflow-y-auto" data-testid="card-details-modal">
        <div className="space-y-4">
          <div>
            <label htmlFor="card-title" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Title
            </label>
            <input
              id="card-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm font-semibold text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>

          <div>
            <label htmlFor="card-details" className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Details
            </label>
            <textarea
              id="card-details"
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              rows={3}
              className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>

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

          <div>
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Labels
            </span>
            <div className="flex flex-wrap gap-2" data-testid="label-picker">
              {ALL_LABELS.map((label) => {
                const style = LABEL_COLORS[label];
                const isSelected = selectedLabels.has(label);
                return (
                  <button
                    key={label}
                    type="button"
                    onClick={() => toggleLabel(label)}
                    className={clsx(
                      "rounded-lg px-2.5 py-1 text-xs font-semibold transition",
                      isSelected
                        ? clsx(style.bg, style.text, "ring-2 ring-offset-1 ring-current")
                        : "bg-[var(--surface)] text-[var(--gray-text)] hover:bg-gray-200"
                    )}
                    aria-pressed={isSelected}
                    data-testid={`toggle-label-${label}`}
                  >
                    {style.name}
                  </button>
                );
              })}
            </div>
          </div>

          {(onAddChecklistItem || (card.checklist && card.checklist.length > 0)) && (
            <div>
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
                Checklist
                {card.checklist && card.checklist.length > 0 && (
                  <span className="ml-2 font-normal normal-case">
                    {card.checklist.filter((i) => i.done).length}/{card.checklist.length}
                  </span>
                )}
              </span>
              <div className="space-y-1" data-testid="checklist-section">
                {(card.checklist || []).map((item) => (
                  <div key={item.id} className="flex items-center gap-2" data-testid={`checklist-${item.id}`}>
                    <button
                      type="button"
                      onClick={() => onToggleChecklistItem?.(item.id)}
                      className={clsx(
                        "flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border transition",
                        item.done
                          ? "border-green-500 bg-green-500 text-white"
                          : "border-[var(--stroke)] hover:border-[var(--primary-blue)]"
                      )}
                      aria-label={`Toggle ${item.text}`}
                      data-testid={`toggle-checklist-${item.id}`}
                    >
                      {item.done && (
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </button>
                    <span className={clsx("flex-1 text-xs", item.done && "text-[var(--gray-text)] line-through")}>
                      {item.text}
                    </span>
                    {onDeleteChecklistItem && (
                      <button
                        type="button"
                        onClick={() => onDeleteChecklistItem(item.id)}
                        className="text-[var(--gray-text)] hover:text-red-500"
                        aria-label={`Delete checklist item ${item.text}`}
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
                {onAddChecklistItem && (
                  <div className="flex gap-2 pt-1">
                    <input
                      type="text"
                      value={newChecklistText}
                      onChange={(e) => setNewChecklistText(e.target.value)}
                      placeholder="Add an item..."
                      className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-1.5 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                      data-testid="checklist-input"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newChecklistText.trim()) {
                          onAddChecklistItem(newChecklistText.trim());
                          setNewChecklistText("");
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newChecklistText.trim()) {
                          onAddChecklistItem(newChecklistText.trim());
                          setNewChecklistText("");
                        }
                      }}
                      className="rounded-xl bg-[var(--primary-blue)] px-3 py-1.5 text-xs font-semibold text-white hover:brightness-110"
                      data-testid="add-checklist-btn"
                    >
                      Add
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {(onAddComment || (card.comments && card.comments.length > 0)) && (
            <div>
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
                Comments
              </span>
              <div className="space-y-2" data-testid="comments-section">
                {(card.comments || []).map((comment) => (
                  <div key={comment.id} className="rounded-xl bg-[var(--surface)] px-3 py-2" data-testid={`comment-${comment.id}`}>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--navy-dark)]">{comment.author}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[var(--gray-text)]">
                          {new Date(comment.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                        </span>
                        {onDeleteComment && (
                          <button
                            type="button"
                            onClick={() => onDeleteComment(comment.id)}
                            className="text-[var(--gray-text)] hover:text-red-500"
                            aria-label={`Delete comment by ${comment.author}`}
                          >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                              <line x1="18" y1="6" x2="6" y2="18" />
                              <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="mt-1 text-xs text-[var(--navy-dark)]">{comment.text}</p>
                  </div>
                ))}
                {onAddComment && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Add a comment..."
                      className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                      data-testid="comment-input"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newComment.trim()) {
                          onAddComment(newComment.trim());
                          setNewComment("");
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newComment.trim()) {
                          onAddComment(newComment.trim());
                          setNewComment("");
                        }
                      }}
                      className="rounded-xl bg-[var(--primary-blue)] px-3 py-2 text-xs font-semibold text-white hover:brightness-110"
                      data-testid="add-comment-btn"
                    >
                      Add
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
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
