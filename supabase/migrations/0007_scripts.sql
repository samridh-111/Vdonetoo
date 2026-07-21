create table scripts (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references batches(id) on delete cascade,
  row_index int not null,
  external_id text,
  title text,
  script_text text not null,
  notes text,
  detected_language_code text references languages(code),
  source_voice_preset text,
  status text not null default 'pending' check (
    status in ('pending', 'validating', 'translating', 'generating', 'uploading', 'completed', 'failed')
  ),
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index ix_scripts_batch on scripts(batch_id);
create index ix_scripts_status on scripts(status);
