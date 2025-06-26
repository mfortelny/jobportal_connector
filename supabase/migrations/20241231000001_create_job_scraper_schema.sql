-- Create companies table
create table companies (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz default now()
);

-- Create positions table
create table positions (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id) on delete cascade,
  title text not null,
  external_job_id text,         -- id z portálu, pro snadné párování
  created_at timestamptz default now()
);

-- Create candidates table
create table candidates (
  id uuid primary key default gen_random_uuid(),
  position_id uuid references positions(id) on delete cascade,
  first_name text, 
  last_name text,
  email text, 
  phone text,
  phone_sha256 text generated always as (encode(digest(phone, 'sha256'), 'hex')) stored,
  source_url text,
  created_at timestamptz default now(),
  unique(position_id, phone_sha256)          -- technická bariéra proti duplicitám
);

-- Add indexes for better performance
create index idx_candidates_position_id on candidates(position_id);
create index idx_positions_company_id on positions(company_id);
create index idx_candidates_phone_sha256 on candidates(phone_sha256); 