"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { getPerson, regenerateFace, repairAgentphone, Person } from "@/lib/api";
import EditPersonModal from "@/components/EditPersonModal";
import Memories from "@/components/Memories";
import SmsThread from "@/components/SmsThread";
import RunLive from "@/components/RunLive";
import RunHistory from "@/components/RunHistory";
import { listRuns, AgentRun } from "@/lib/api";

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isLoaded } = useUser();
  const [person, setPerson] = useState<Person | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [repairing, setRepairing] = useState(false);

  async function handleRepairAgentphone() {
    if (!user || !id || !person) return;
    setRepairing(true);
    setError(null);
    try {
      const res = await repairAgentphone(user.id, id as string);
      if (res.agent_id) {
        setPerson({ ...person, agentphone_agent_id: res.agent_id });
      }
      if (!res.webhook_set) {
        setError(
          res.webhook_url
            ? "Agent ready, but webhook setup failed — check backend logs."
            : "PUBLIC_WEBHOOK_BASE is not set on the backend; SMS won’t trigger runs until it is.",
        );
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Repair failed");
    } finally {
      setRepairing(false);
    }
  }

  useEffect(() => {
    if (!user || !id) return;
    let cancelled = false;
    async function tick() {
      try {
        const r = await listRuns(user!.id, id as string);
        if (!cancelled) setRuns(r);
      } catch {
        // ignore polling errors
      }
    }
    tick();
    const t = setInterval(tick, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [user, id]);

  const mostRecentRun = runs[0] || null;
  const previousRuns = runs.slice(1);

  async function handleRegenerate() {
    if (!user || !id) return;
    setRegenerating(true);
    setError(null);
    try {
      const updated = await regenerateFace(user.id, id);
      setPerson(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Regenerate failed");
    } finally {
      setRegenerating(false);
    }
  }

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
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn btn-ghost"
            onClick={handleRepairAgentphone}
            disabled={repairing}
            title="Re-register the AgentPhone webhook so inbound SMS triggers runs"
          >
            {repairing
              ? "Repairing…"
              : person.agentphone_agent_id
                ? "Re-register webhook"
                : "Repair AgentPhone"}
          </button>
          <button className="btn btn-ghost" onClick={() => setEditOpen(true)}>
            Edit
          </button>
          <button
            className="btn btn-gold"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            {regenerating ? "Regenerating…" : "Regenerate face"}
          </button>
        </div>
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
            <h3>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="https://logo.clearbit.com/paysponge.com" alt="" className="brand-logo" />
              Bank / Wallet (Sponge)
            </h3>
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
              <dt>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="https://logo.clearbit.com/agentmail.to" alt="" className="brand-logo" />
                AgentMail
              </dt>
              <dd>{person.email || "—"}</dd>
              <dt>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="https://logo.clearbit.com/agentphone.ai" alt="" className="brand-logo" />
                AgentPhone
              </dt>
              <dd>{person.phone || "—"}</dd>
            </dl>
          </div>

          <div className="section">
            <h3>Face prompt</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
              {person.face_prompt || "—"}
            </p>
          </div>

          {user && <SmsThread ownerId={user.id} personId={person.id} />}
          <RunLive run={mostRecentRun} />
          <RunHistory runs={previousRuns} />
          {user && <Memories ownerId={user.id} personId={person.id} />}
        </div>
      </div>

      {editOpen && user && (
        <EditPersonModal
          ownerId={user.id}
          person={person}
          onClose={() => setEditOpen(false)}
          onSaved={(p) => {
            setPerson(p);
            setEditOpen(false);
          }}
        />
      )}
    </>
  );
}
