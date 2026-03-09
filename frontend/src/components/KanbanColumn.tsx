import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, CardLabel, Column } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

const columnAccentColors = [
  "bg-[var(--primary-blue)]",
  "bg-[var(--accent-yellow)]",
  "bg-[var(--secondary-purple)]",
  "bg-[#34a77f]",
  "bg-[#e86c5f]",
];

type KanbanColumnProps = {
  column: Column;
  cards: Card[];
  columnIndex: number;
  onRename: (columnId: string, title: string) => void;
  onAddCard: (columnId: string, title: string, details: string) => void;
  onDeleteCard: (columnId: string, cardId: string) => void;
  onUpdateCard?: (cardId: string, updates: { title?: string; details?: string; priority?: "low" | "medium" | "high" | null; due_date?: string | null; labels?: CardLabel[] }) => void;
  onDeleteColumn?: (columnId: string) => void;
  onAddComment?: (cardId: string, text: string) => void;
  onDeleteComment?: (cardId: string, commentId: string) => void;
};

export const KanbanColumn = ({
  column,
  cards,
  columnIndex,
  onRename,
  onAddCard,
  onDeleteCard,
  onUpdateCard,
  onDeleteColumn,
  onAddComment,
  onDeleteComment,
}: KanbanColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });
  const accentColor = columnAccentColors[columnIndex % columnAccentColors.length];

  return (
    <section
      ref={setNodeRef}
      className={clsx(
        "flex min-h-[480px] flex-col rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3 transition",
        isOver && "ring-2 ring-[var(--accent-yellow)]"
      )}
      data-testid={`column-${column.id}`}
    >
      <div className="mb-3">
        <div className="flex items-center gap-2">
          <div className={clsx("h-2 w-2 rounded-full", accentColor)} />
          <h3 className="sr-only">{column.title}</h3>
          <input
            value={column.title}
            onChange={(event) => onRename(column.id, event.target.value)}
            className="min-w-0 flex-1 bg-transparent font-display text-sm font-semibold text-[var(--navy-dark)] outline-none"
            aria-label={`Title for ${column.title}`}
          />
          <span className="flex-shrink-0 rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold tabular-nums text-[var(--gray-text)]">
            {cards.length}
          </span>
          {onDeleteColumn && (
            <button
              type="button"
              onClick={() => onDeleteColumn(column.id)}
              className="flex-shrink-0 rounded-lg p-1 text-[var(--gray-text)] opacity-0 transition group-hover:opacity-100 hover:bg-red-50 hover:text-red-500"
              aria-label={`Delete column ${column.title}`}
              data-testid={`delete-column-${column.id}`}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2">
        <SortableContext items={column.cardIds} strategy={verticalListSortingStrategy}>
          {cards.map((card) => (
            <KanbanCard
              key={card.id}
              card={card}
              onDelete={(cardId) => onDeleteCard(column.id, cardId)}
              onUpdateCard={onUpdateCard}
              onAddComment={onAddComment}
              onDeleteComment={onDeleteComment}
            />
          ))}
        </SortableContext>
        {cards.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-[var(--stroke)] px-3 py-6 text-center text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Drop a card here
          </div>
        )}
      </div>
      <NewCardForm
        onAdd={(title, details) => onAddCard(column.id, title, details)}
      />
    </section>
  );
};
