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
      <button className="wall-close" onClick={onClose} aria-label="Close">✕</button>
      {error && <div className="wall-error">{error}</div>}
      <div className="wall-grid">
        {Array.from({ length: 16 }).map((_, i) => {
          const v = items[i];
          return (
            <div key={v?.id || `slot-${i}`} className="wall-cell">
              {v?.video_url && (
                <video
                  src={v.video_url}
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="auto"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
