create table translations (
  id uuid primary key default gen_random_uuid(),
  script_id uuid not null references scripts(id) on delete cascade,
  source_language_code text references languages(code),
  target_language_code text not null references languages(code),
  provider text not null check (provider in ('openai', 'gemini', 'none')),
  translated_text text,
  status text not null default 'pending' check (status in ('pending', 'completed', 'failed')),
  error_message text,
  created_at timestamptz not null default now()
);

create index ix_translations_script on translations(script_id);
