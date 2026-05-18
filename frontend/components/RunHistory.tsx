"use client";

import { AgentRun } from "@/lib/api";

function VideoSlot({ url, label }: { url: string | null; label: string }) {
  return (
    <div className="run-video">
      <div className="run-video-label">
        <span aria-hidden>🎥</span> {label}
      </div>
      {url ? (
        <video src={url} controls preload="metadata" />
      ) : (
        <div className="run-video-placeholder">video pending…</div>
      )}
    </div>
  );
}

export default function RunHistory({ runs }: { runs: AgentRun[] }) {
  return (
    <div className="section">
      <h3>Run history</h3>
      {runs.length === 0 ? (
        <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>No runs yet.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {runs.map((r) => (
            <div key={r.id} className="run-row">
              <div className="run-top">
                <span className={`pill pill-${r.status}`}>{r.status}</span>
                <span className="run-time">
                  {new Date(r.created_at).toLocaleString()}
                </span>
              </div>
              {r.trigger_text && <div className="run-trigger">“{r.trigger_text}”</div>}
              <div className="run-videos">
                <VideoSlot url={r.intro_video_url} label="Intro" />
                <VideoSlot url={r.outro_video_url} label="Outro" />
              </div>
              {r.result && <div className="run-result">{r.result}</div>}
              {r.bu_live_url && r.status === "running" && (
                <a className="run-link" href={r.bu_live_url} target="_blank" rel="noreferrer">
                  Open live view →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
