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
  agentphone_agent_id text,
  sponge_agent_id text,
  sponge_wallet_address text,
  sponge_api_key text,
  face_url text,
  face_prompt text,
  credentials_text text,
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

create table if not exists agent_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  person_id uuid not null references people(id) on delete cascade,
  trigger_text text,
  bu_session_id text,
  bu_live_url text,
  status text not null default 'running',
  result text,
  intro_video_url text,
  outro_video_url text,
  created_at timestamptz not null default now()
);

create index if not exists agent_runs_owner_person_idx on agent_runs (owner_id, person_id, created_at desc);
create index if not exists agent_runs_status_idx on agent_runs (status);

create table if not exists ugc_videos (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  person_id uuid not null references people(id) on delete cascade,
  prompt text not null,
  video_url text,
  status text not null default 'generating',
  created_at timestamptz not null default now()
);

create index if not exists ugc_videos_owner_person_idx on ugc_videos (owner_id, person_id, created_at desc);
