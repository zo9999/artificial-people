"use client";

import { AgentRun } from "@/lib/api";

function VideoCell({ url, label }: { url: string | null; label: string }) {
  return (
    <div className="run-video">
      <div className="run-video-label">
        <span aria-hidden>🎥</span> {label}
      </div>
      {url ? (
        <video src={url} autoPlay playsInline controls preload="auto" />
      ) : (
        <div className="run-video-placeholder">video pending…</div>
      )}
    </div>
  );
}

export default function RunLive({ run }: { run: AgentRun | null }) {
  return (
    <div className="section">
      <h3>Live browser</h3>
      {run ? (
        <div className="active-run">
          <div className="active-run-left">
            <div className="live-meta">
              <span className={`pill pill-${run.status}`}>{run.status}</span>
              <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                {run.trigger_text}
              </span>
            </div>
            {run.bu_live_url ? (
              <iframe
                className="live-frame"
                src={run.bu_live_url}
                allow="clipboard-read; clipboard-write"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
              />
            ) : (
              <div className="live-frame-placeholder">browser idle</div>
            )}
          </div>
          <div className="active-run-right">
            <VideoCell url={run.intro_video_url} label="Intro" />
            <VideoCell url={run.outro_video_url} label="Outro" />
          </div>
        </div>
      ) : (
        <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Idle. Text the AP’s phone number to start a run.
        </div>
      )}
    </div>
  );
}
