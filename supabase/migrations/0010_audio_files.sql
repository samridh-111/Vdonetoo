create table audio_files (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references jobs(id) on delete cascade,
  script_id uuid not null references scripts(id) on delete cascade,
  batch_id uuid not null references batches(id) on delete cascade,
  language_code text not null references languages(code),
  voice_id uuid references voices(id),
  storage_path text not null,
  public_url text,
  duration_seconds numeric(6, 2),
  file_size_bytes bigint,
  generation_time_ms int,
  created_at timestamptz not null default now()
);

create index ix_audio_files_batch on audio_files(batch_id);
create index ix_audio_files_job on audio_files(job_id);
