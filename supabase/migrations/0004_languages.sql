-- Extensible language registry. Adding a new supported language later is a
-- single INSERT here -- no code changes to detection, translation, or upload
-- column-matching logic are required.
create table languages (
  code text primary key,                              -- ISO 639-1, e.g. 'hi'
  name text not null,                                  -- 'Hindi'
  locale text,                                         -- 'hi-IN'
  detector_aliases text[] not null default '{}',       -- codes the language detector may return for this language
  header_synonyms text[] not null default '{}',        -- synonyms recognized when auto-detecting the CSV/XLSX Language column
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
