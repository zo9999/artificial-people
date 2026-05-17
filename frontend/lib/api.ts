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
  agentphone_agent_id: string | null;
  sponge_agent_id: string | null;
  sponge_wallet_address: string | null;
  face_url: string | null;
  face_prompt: string | null;
  created_at: string;
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const body = JSON.parse(text);
      const msg = body.message || body.error || text;
      detail = body.service ? `[${body.service}] ${msg}` : msg;
    } catch {
      // not JSON; keep raw text
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

export type Memory = {
  id: string | null;
  content: string;
  score?: number | null;
  created_at?: string | null;
};

export type AgentRun = {
  id: string;
  owner_id: string;
  person_id: string;
  trigger_text: string | null;
  bu_session_id: string | null;
  bu_live_url: string | null;
  status: "running" | "succeeded" | "failed";
  result: string | null;
  created_at: string;
};

export type SmsMessage = {
  id: string | null;
  from: string | null;
  to: string | null;
  body: string;
  direction: "in" | "out";
  created_at: string | null;
};

export async function listRuns(ownerId: string, personId: string): Promise<AgentRun[]> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(personId)}/runs?owner_id=${encodeURIComponent(ownerId)}`,
    { cache: "no-store" },
  );
  return handle<AgentRun[]>(r);
}

export async function listSmsMessages(
  ownerId: string,
  personId: string,
): Promise<SmsMessage[]> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(personId)}/messages?owner_id=${encodeURIComponent(ownerId)}`,
    { cache: "no-store" },
  );
  return handle<SmsMessage[]>(r);
}

export async function listMemories(
  ownerId: string,
  personId: string,
  q?: string,
): Promise<Memory[]> {
  const params = new URLSearchParams({ owner_id: ownerId });
  if (q) params.set("q", q);
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(personId)}/memories?${params.toString()}`,
    { cache: "no-store" },
  );
  return handle<Memory[]>(r);
}

export async function addMemory(
  ownerId: string,
  personId: string,
  content: string,
): Promise<Memory> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(personId)}/memories`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ owner_id: ownerId, content }),
    },
  );
  return handle<Memory>(r);
}

export async function updatePerson(
  ownerId: string,
  id: string,
  patch: Partial<Pick<Person, "first_name" | "last_name" | "address" | "face_prompt">>,
): Promise<Person> {
  const r = await fetch(`${BASE}/api/people/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner_id: ownerId, ...patch }),
  });
  return handle<Person>(r);
}

export async function repairAgentphone(
  ownerId: string,
  id: string,
): Promise<{
  ok: boolean;
  agent_id?: string;
  created_new?: boolean;
  webhook_url?: string | null;
  webhook_set?: boolean;
}> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(id)}/repair-agentphone`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ owner_id: ownerId }),
    },
  );
  return handle(r);
}

export async function regenerateFace(
  ownerId: string,
  id: string,
  facePrompt?: string,
): Promise<Person> {
  const r = await fetch(
    `${BASE}/api/people/${encodeURIComponent(id)}/regenerate-face`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        owner_id: ownerId,
        ...(facePrompt ? { face_prompt: facePrompt } : {}),
      }),
    },
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
