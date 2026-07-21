-- One row per (script x target-language) audio unit -- this is the fan-out
-- unit for concurrent Celery processing.
create table jobs (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references batches(id) on delete cascade,
  script_id uuid not null references scripts(id) on delete cascade,
  translation_id uuid references translations(id),
  language_code text not null references languages(code),
  voice_id uuid references voices(id),
  celery_task_id text,
  stage text not null default 'queued' check (
    stage in ('queued', 'preparing', 'translating', 'generating', 'uploading', 'completed', 'failed', 'retrying')
  ),
  attempt int not null default 0,
  max_attempts int not null default 3,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index ix_jobs_batch on jobs(batch_id);
create index ix_jobs_script on jobs(script_id);
create index ix_jobs_stage on jobs(stage);
