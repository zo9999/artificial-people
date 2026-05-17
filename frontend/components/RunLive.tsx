"use client";

import { AgentRun } from "@/lib/api";

export default function RunLive({ run }: { run: AgentRun | null }) {
  return (
    <div className="section">
      <h3>Live browser</h3>
      {run && run.bu_live_url ? (
        <div className="live-frame-wrap">
          <div className="live-meta">
            <span className={`pill pill-${run.status}`}>{run.status}</span>
            <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              {run.trigger_text}
            </span>
          </div>
          <iframe
            className="live-frame"
            src={run.bu_live_url}
            allow="clipboard-read; clipboard-write"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </div>
      ) : (
        <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Idle. Text the AP’s phone number to start a run.
        </div>
      )}
    </div>
  );
}
