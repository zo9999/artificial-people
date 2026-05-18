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

  const playable = items.filter((v) => v?.video_url);
  // Duplicate the list so the marquee can loop seamlessly
  const loop = playable.length > 0 ? [...playable, ...playable] : [];

  return (
    <div className="wall">
      <button className="wall-close" onClick={onClose} aria-label="Close">✕</button>
      {error && <div className="wall-error">{error}</div>}
      <div className="wall-carousel">
        <div
          className="wall-track"
          style={{
            animationDuration: `${Math.max(20, playable.length * 6)}s`,
          }}
        >
          {loop.map((v, i) => (
            <div key={`${v.id}-${i}`} className="wall-cell">
              <video
                src={v.video_url!}
                autoPlay
                muted
                loop
                playsInline
                preload="auto"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
