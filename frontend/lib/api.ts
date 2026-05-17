const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export type Person = {
  id: string;
  owner_id: string;
  first_name: string;
  last_name: string;
  address: string;
  email: string | null;
  phone: string | null;
  agentmail_inbox_id: string | null;
  agentphone_number_id: string | null;
  sponge_agent_id: string | null;
  sponge_wallet_address: string | null;
  face_url: string | null;
  face_prompt: string | null;
  created_at: string;
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: string;
    try {
      const body = await res.json();
      detail = body.message || body.error || JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function listPeople(ownerId: string): Promise<Person[]> {
  const r = await fetch(`${BASE}/api/people?owner_id=${encodeURIComponent(ownerId)}`, {
    cache: "no-store",
  });
  return handle<Person[]>(r);
}

export async function getPerson(ownerId: string, id: string): Promise<Person> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(id)}?owner_id=${encodeURIComponent(ownerId)}`,
    { cache: "no-store" },
  );
  return handle<Person>(r);
}

export async function createPerson(
  ownerId: string,
  payload: {
    first_name: string;
    last_name: string;
    address: string;
    face_prompt: string;
  },
): Promise<Person> {
  const r = await fetch(`${BASE}/api/people`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner_id: ownerId, ...payload }),
  });
  return handle<Person>(r);
}
