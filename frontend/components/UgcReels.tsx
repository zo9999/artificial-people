"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listUgc, createUgc, uploadUgc, UgcVideo } from "@/lib/api";

function PromptModal({
  onClose,
  onSubmit,
  submitting,
}: {
  onClose: () => void;
  onSubmit: (prompt: string) => Promise<void>;
  submitting: boolean;
}) {
  const [prompt, setPrompt] = useState("");
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={async (e) => {
          e.preventDefault();
          if (!prompt.trim()) return;
          await onSubmit(prompt.trim());
        }}
      >
        <h2>Generate UGC reel</h2>
        <div className="field">
          <label>What should they do / say in the reel?</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. holding up an iced matcha and saying 'finally got my hands on this!'"
            style={{ minHeight: 110 }}
            required
          />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn-gold" disabled={submitting || !prompt.trim()}>
            {submitting ? "Starting…" : "Generate"}
          </button>
        </div>
      </form>
    </div>
  );
}

function ExpandedGallery({
  items,
  onClose,
}: {
  items: UgcVideo[];
  onClose: () => void;
}) {
  return (
    <div className="ugc-fullscreen">
      <div className="ugc-fullscreen-header">
        <div>
          <strong>UGC Reels</strong>
          <span style={{ color: "var(--muted)", marginLeft: 8, fontSize: "0.85rem" }}>
            {items.length} total
          </span>
        </div>
        <button className="btn btn-ghost" onClick={onClose}>✕ Close</button>
      </div>
      <div className="ugc-grid">
        {items.map((v) => (
          <div key={v.id} className="ugc-card">
            {v.video_url ? (
              <video src={v.video_url} controls playsInline preload="metadata" />
            ) : (
              <div className="ugc-placeholder">
                {v.status === "failed" ? "failed" : "generating…"}
              </div>
            )}
            <div className="ugc-card-meta">“{v.prompt}”</div>
          </div>
        ))}
        {items.length === 0 && (
          <div style={{ color: "var(--muted)" }}>No reels yet.</div>
        )}
      </div>
    </div>
  );
}

export default function UgcReels({
  ownerId,
  personId,
}: {
  ownerId: string;
  personId: string;
}) {
  const [items, setItems] = useState<UgcVideo[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setItems(await listUgc(ownerId, personId));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load UGC");
    }
  }, [ownerId, personId]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  async function handleSubmit(prompt: string) {
    setSubmitting(true);
    setError(null);
    try {
      await createUgc(ownerId, personId, prompt);
      setModalOpen(false);
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generate failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const f of Array.from(files)) {
        if (!f.type.startsWith("video/")) continue;
        await uploadUgc(ownerId, personId, f, f.name);
      }
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="section">
      <div className="ugc-header">
        <h3 style={{ marginBottom: 0 }}>🎬 UGC Reels</h3>
        <div style={{ display: "flex", gap: 8 }}>
          {items.length > 0 && (
            <button className="btn btn-ghost" onClick={() => setGalleryOpen(true)}>
              ⤢ View all ({items.length})
            </button>
          )}
          <button className="btn btn-gold" onClick={() => setModalOpen(true)}>
            + Generate UGC
          </button>
        </div>
      </div>
      {error && <div className="error">{error}</div>}

      <div
        className={`ugc-dropzone${dragOver ? " drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        {uploading ? "Uploading…" : "📁 Drop a video here, or click to upload"}
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          multiple
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {items.length === 0 ? (
        <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          No reels yet. Hit <strong>Generate UGC</strong> or drop a video above.
        </div>
      ) : (
        <div className="ugc-row">
          {items.map((v) => (
            <div key={v.id} className="ugc-card">
              {v.video_url ? (
                <video
                  src={v.video_url}
                  controls
                  playsInline
                  preload="metadata"
                />
              ) : (
                <div className="ugc-placeholder">
                  {v.status === "failed" ? "failed" : "generating…"}
                </div>
              )}
              <div className="ugc-card-meta">“{v.prompt}”</div>
            </div>
          ))}
        </div>
      )}

      {modalOpen && (
        <PromptModal
          onClose={() => !submitting && setModalOpen(false)}
          onSubmit={handleSubmit}
          submitting={submitting}
        />
      )}
      {galleryOpen && <ExpandedGallery items={items} onClose={() => setGalleryOpen(false)} />}
    </div>
  );
}
