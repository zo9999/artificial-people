"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { getPerson, Person } from "@/lib/api";

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isLoaded } = useUser();
  const [person, setPerson] = useState<Person | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded || !user || !id) return;
    (async () => {
      try {
        setPerson(await getPerson(user.id, id));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    })();
  }, [isLoaded, user, id]);

  if (loading) return <div className="loading">Loading…</div>;
  if (error) return <div className="error">{error}</div>;
  if (!person) return <div className="empty">Not found.</div>;

  return (
    <>
      <div className="page-header">
        <Link href="/" className="btn btn-ghost">
          ← Back
        </Link>
      </div>

      <div className="detail">
        {person.face_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            className="detail-face"
            src={person.face_url}
            alt={`${person.first_name} ${person.last_name}`}
          />
        ) : (
          <div className="detail-face" />
        )}
        <div>
          <span className="detail-uuid">AP {person.id}</span>
          <h2>
            {person.first_name} {person.last_name}
          </h2>

          <div className="section">
            <h3>Identity</h3>
            <dl className="kv">
              <dt>Email</dt>
              <dd>{person.email || "—"}</dd>
              <dt>Phone</dt>
              <dd>{person.phone || "—"}</dd>
              <dt>Address</dt>
              <dd>{person.address}</dd>
            </dl>
          </div>

          <div className="section">
            <h3>Bank / Wallet (Sponge)</h3>
            <dl className="kv">
              <dt>Agent ID</dt>
              <dd>{person.sponge_agent_id || "—"}</dd>
              <dt>Wallet address</dt>
              <dd>{person.sponge_wallet_address || "—"}</dd>
            </dl>
          </div>

          <div className="section">
            <h3>Services</h3>
            <dl className="kv">
              <dt>AgentMail inbox</dt>
              <dd>{person.agentmail_inbox_id || "—"}</dd>
              <dt>AgentPhone number ID</dt>
              <dd>{person.agentphone_number_id || "—"}</dd>
            </dl>
          </div>

          <div className="section">
            <h3>Face prompt</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
              {person.face_prompt || "—"}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
