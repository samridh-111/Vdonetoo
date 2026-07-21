create table batches (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id),
  name text not null,
  source_type text not null check (source_type in ('csv', 'xlsx', 'google_sheet')),
  source_filename text,
  source_url text,
  translation_mode text not null check (
    translation_mode in ('keep_original', 'translate_everything', 'translate_selected', 'generate_multiple')
  ),
  target_languages text[] not null default '{}',
  translation_provider text not null check (translation_provider in ('openai', 'gemini')),
  default_voice_map jsonb not null default '{}',       -- {"hi": "<voice_id>", "ta": "<voice_id>"}
  status text not null default 'draft' check (
    status in ('draft', 'queued', 'processing', 'completed', 'failed', 'cancelled')
  ),
  concurrency_limit int not null default 8,
  total_scripts int not null default 0,
  total_jobs int not null default 0,
  completed_jobs int not null default 0,
  failed_jobs int not null default 0,
  zip_storage_path text,
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz not null default now()
);

create index ix_batches_project on batches(project_id);
create index ix_batches_status on batches(status);
