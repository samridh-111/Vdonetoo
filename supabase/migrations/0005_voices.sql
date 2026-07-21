create table voices (
  id uuid primary key default gen_random_uuid(),
  name text not null,                                  -- 'Vedantu Female'
  preset_key text unique not null,                     -- 'vedantu_female'
  elevenlabs_voice_id text not null,
  language_code text references languages(code),
  similarity numeric(3, 2) not null default 0.75,
  stability numeric(3, 2) not null default 0.50,
  style numeric(3, 2) not null default 0.00,
  speed numeric(3, 2) not null default 1.00,
  sample_audio_url text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index ix_voices_language on voices(language_code);
