"use client";

import { useEffect, useState, useCallback } from "react";
import { useUser } from "@clerk/nextjs";
import PersonCard from "@/components/PersonCard";
import NewPersonModal from "@/components/NewPersonModal";
import AllUgcWall from "@/components/AllUgcWall";
import { listPeople, Person } from "@/lib/api";

export default function PeoplePage() {
  const { user, isLoaded } = useUser();
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [wallOpen, setWallOpen] = useState(false);

  const refresh = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      setPeople(await listPeople(user.id));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (isLoaded && user) refresh();
  }, [isLoaded, user, refresh]);

  return (
    <>
      <div className="page-header">
        <h1>People</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-gold" onClick={() => setWallOpen(true)}>
            🎬 Wall
          </button>
          <button className="btn" onClick={() => setModalOpen(true)}>
            + New Person
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="loading">Loading…</div>
      ) : people.length === 0 ? (
        <div className="empty">
          No people yet. Click <strong>+ New Person</strong> to create one.
        </div>
      ) : (
        <div className="grid">
          {people.map((p) => (
            <PersonCard key={p.id} person={p} />
          ))}
        </div>
      )}

      {modalOpen && user && (
        <NewPersonModal
          ownerId={user.id}
          onClose={() => setModalOpen(false)}
          onCreated={() => {
            setModalOpen(false);
            refresh();
          }}
        />
      )}

      {wallOpen && user && (
        <AllUgcWall ownerId={user.id} onClose={() => setWallOpen(false)} />
      )}
    </>
  );
}
