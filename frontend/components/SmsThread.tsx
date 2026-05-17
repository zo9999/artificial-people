"use client";

import { useEffect, useState } from "react";
import { listSmsMessages, SmsMessage } from "@/lib/api";

export default function SmsThread({
  ownerId,
  personId,
}: {
  ownerId: string;
  personId: string;
}) {
  const [items, setItems] = useState<SmsMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function tick() {
      try {
        const m = await listSmsMessages(ownerId, personId);
        if (!cancelled) {
          setItems(m);
          setError(null);
        }
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load SMS");
      }
    }
    tick();
    const t = setInterval(tick, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [ownerId, personId]);

  return (
    <div className="section">
      <h3>SMS</h3>
      {error && <div className="error">{error}</div>}
      {items.length === 0 ? (
        <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>No messages yet.</div>
      ) : (
        <div className="sms-thread">
          {items.map((m, i) => (
            <div key={m.id || i} className={`sms-bubble sms-${m.direction}`}>
              <div>{m.body}</div>
              {m.created_at && (
                <div className="sms-meta">{new Date(m.created_at).toLocaleString()}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
