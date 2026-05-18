"use client";

import { AgentRun } from "@/lib/api";

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
              {(r.intro_video_url || r.outro_video_url) && (
                <div className="run-videos">
                  {r.intro_video_url && (
                    <div className="run-video">
                      <div className="run-video-label">Intro</div>
                      <video src={r.intro_video_url} controls preload="metadata" />
                    </div>
                  )}
                  {r.outro_video_url && (
                    <div className="run-video">
                      <div className="run-video-label">Outro</div>
                      <video src={r.outro_video_url} controls preload="metadata" />
                    </div>
                  )}
                </div>
              )}
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
