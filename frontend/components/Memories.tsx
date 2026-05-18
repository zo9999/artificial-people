"use client";

import { useEffect, useState, useCallback } from "react";
import { listMemories, addMemory, Memory } from "@/lib/api";

export default function Memories({
  ownerId,
  personId,
}: {
  ownerId: string;
  personId: string;
}) {
  const [items, setItems] = useState<Memory[]>([]);
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(
    async (q?: string) => {
      setLoading(true);
      setError(null);
      try {
        setItems(await listMemories(ownerId, personId, q));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load memories");
      } finally {
        setLoading(false);
      }
    },
    [ownerId, personId],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    setError(null);
    try {
      await addMemory(ownerId, personId, draft.trim());
      setDraft("");
      await refresh(query.trim() || undefined);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Add failed");
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    await refresh(query.trim() || undefined);
  }

  return (
    <div className="section">
      <h3>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="https://logo.clearbit.com/supermemory.ai"
          alt=""
          className="brand-logo"
        />
        Memories
      </h3>
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleAdd} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <textarea
          className="memory-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Log something this person did or learned…"
          rows={2}
        />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button type="submit" className="btn" disabled={!draft.trim()}>
            Add memory
          </button>
        </div>
      </form>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <input
          className="memory-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories…"
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-ghost">
          Search
        </button>
      </form>

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
        {loading ? (
          <div className="loading">Loading…</div>
        ) : items.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>No memories yet.</div>
        ) : (
          items.map((m, i) => (
            <div key={m.id || i} className="memory-row">
              <div>{m.content}</div>
              {m.created_at && (
                <div className="memory-meta">
                  {new Date(m.created_at).toLocaleString()}
                  {typeof m.score === "number" ? ` · score ${m.score.toFixed(2)}` : ""}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
