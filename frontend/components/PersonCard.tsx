"use client";

import Link from "next/link";
import { Person } from "@/lib/api";

export default function PersonCard({ person }: { person: Person }) {
  return (
    <Link href={`/people/${person.id}`} className="card">
      {person.face_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className="card-face"
          src={person.face_url}
          alt={`${person.first_name} ${person.last_name}`}
        />
      ) : (
        <div className="card-face" />
      )}
      <div className="card-body">
        <div className="card-name">
          {person.first_name} {person.last_name}
        </div>
        {person.email && <div className="card-meta">{person.email}</div>}
        {person.phone && <div className="card-meta">{person.phone}</div>}
        {person.address && <div className="card-meta">{person.address}</div>}
      </div>
    </Link>
  );
}
