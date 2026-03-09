"use client";

import { useState } from "react";
import { BoardDashboard } from "@/components/BoardDashboard";
import { KanbanBoard } from "@/components/KanbanBoard";

export default function Home() {
  const [selectedBoardId, setSelectedBoardId] = useState<number | null>(null);

  if (selectedBoardId !== null) {
    return (
      <KanbanBoard
        boardId={selectedBoardId}
        onBack={() => setSelectedBoardId(null)}
      />
    );
  }

  return <BoardDashboard onSelectBoard={setSelectedBoardId} />;
}
