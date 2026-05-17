"use client";

import { useState } from "react";
import { createPerson } from "@/lib/api";

export default function NewPersonModal({
  ownerId,
  onClose,
  onCreated,
}: {
  ownerId: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [address, setAddress] = useState("");
  const [facePrompt, setFacePrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createPerson(ownerId, {
        first_name: firstName,
        last_name: lastName,
        address,
        face_prompt: facePrompt,
      });
      onCreated();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Create failed");
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>New Artificial Person</h2>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>First name</label>
          <input
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label>Last name</label>
          <input
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label>Address</label>
          <input
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="1 Mayfair St, London"
            required
          />
        </div>
        <div className="field">
          <label>Face prompt</label>
          <textarea
            value={facePrompt}
            onChange={(e) => setFacePrompt(e.target.value)}
            placeholder="a thoughtful woman in her 30s, brown hair, warm smile"
            required
          />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn" disabled={submitting}>
            {submitting ? "Creating…" : "Create person"}
          </button>
        </div>
      </form>
    </div>
  );
}
