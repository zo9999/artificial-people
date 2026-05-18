"use client";

import { useCallback, useEffect, useState } from "react";
import { listAllUgc, UgcVideo } from "@/lib/api";

export default function AllUgcWall({
  ownerId,
  onClose,
}: {
  ownerId: string;
  onClose: () => void;
}) {
  const [items, setItems] = useState<UgcVideo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setItems(await listAllUgc(ownerId, 16));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load reels");
    }
  }, [ownerId]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 8000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <div className="wall">
      <div className="wall-bg">
        <div className="wall-cloud cloud-a" />
        <div className="wall-cloud cloud-b" />
        <div className="wall-cloud cloud-c" />
        <div className="wall-cloud cloud-d" />
        <div className="wall-cloud cloud-e" />
      </div>
      <div className="wall-header">
        <div className="wall-title">All Artificial People — UGC Wall</div>
        <button className="btn btn-ghost" onClick={onClose}>✕ Close</button>
      </div>
      {error && <div className="error" style={{ position: "relative", zIndex: 2 }}>{error}</div>}
      <div className="wall-grid">
        {Array.from({ length: 16 }).map((_, i) => {
          const v = items[i];
          return (
            <div key={v?.id || `slot-${i}`} className="wall-cell">
              {v?.video_url ? (
                <video
                  src={v.video_url}
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="auto"
                />
              ) : (
                <div className="wall-empty" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
