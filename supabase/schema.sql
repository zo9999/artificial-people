-- Artificial People (AP) v1 schema
-- Apply in Supabase SQL editor. Also create a public Storage bucket named 'faces'.

create extension if not exists "pgcrypto";

create table if not exists people (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  first_name text not null,
  last_name text not null,
  address text not null,
  email text,
  agentmail_inbox_id text,
  phone text,
  agentphone_number_id text,
  sponge_agent_id text,
  sponge_wallet_address text,
  sponge_api_key text,
  face_url text,
  face_prompt text,
  created_at timestamptz not null default now()
);

create index if not exists people_owner_id_idx on people (owner_id);
create index if not exists people_owner_created_idx on people (owner_id, created_at desc);

create table if not exists memories (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  person_id uuid not null references people(id) on delete cascade,
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists memories_person_idx on memories (person_id, created_at desc);
