create table logs (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references batches(id) on delete cascade,
  script_id uuid references scripts(id) on delete set null,
  job_id uuid references jobs(id) on delete set null,
  level text not null default 'info' check (level in ('info', 'warning', 'error')),
  message text not null,
  context jsonb,
  created_at timestamptz not null default now()
);

create index ix_logs_batch on logs(batch_id, created_at);
