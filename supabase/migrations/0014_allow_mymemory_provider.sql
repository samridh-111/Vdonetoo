-- Adds MyMemory as a valid translation_provider value (a free, keyless
-- stand-in provider used ahead of OpenAI/Gemini billing being set up).
alter table batches drop constraint batches_translation_provider_check;
alter table batches add constraint batches_translation_provider_check
  check (translation_provider in ('openai', 'gemini', 'mymemory'));

alter table translations drop constraint translations_provider_check;
alter table translations add constraint translations_provider_check
  check (provider in ('openai', 'gemini', 'mymemory', 'none'));
