"use client";

import { useState } from "react";
import { updatePerson, Person } from "@/lib/api";

export default function EditPersonModal({
  ownerId,
  person,
  onClose,
  onSaved,
}: {
  ownerId: string;
  person: Person;
  onClose: () => void;
  onSaved: (p: Person) => void;
}) {
  const [firstName, setFirstName] = useState(person.first_name);
  const [lastName, setLastName] = useState(person.last_name);
  const [address, setAddress] = useState(person.address);
  const [facePrompt, setFacePrompt] = useState(person.face_prompt || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updatePerson(ownerId, person.id, {
        first_name: firstName,
        last_name: lastName,
        address,
        face_prompt: facePrompt,
      });
      onSaved(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>Edit person</h2>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>First name</label>
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Last name</label>
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Address</label>
          <input value={address} onChange={(e) => setAddress(e.target.value)} required />
        </div>
        <div className="field">
          <label>Face prompt</label>
          <textarea
            value={facePrompt}
            onChange={(e) => setFacePrompt(e.target.value)}
            placeholder="Used the next time you regenerate the face."
          />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className="btn" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
