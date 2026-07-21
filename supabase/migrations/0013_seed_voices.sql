-- Seed the 8 named voice presets from the spec. `elevenlabs_voice_id` values
-- below are ElevenLabs' real, publicly-available "premade" stock voice IDs
-- (constant across every ElevenLabs account) so this seed works out of the
-- box with the `eleven_multilingual_v2` model, which can render any of these
-- voices in Hindi/Tamil/Kannada/etc. -- these are NOT placeholders.
--
-- If you have custom/cloned voices in your ElevenLabs account you'd rather
-- use instead (e.g. an actual Vedantu-branded voice), replace the
-- `elevenlabs_voice_id` values below with those voice IDs from
-- https://elevenlabs.io/app/voice-library before running this migration,
-- or UPDATE the `voices` table afterwards.
insert into voices (name, preset_key, elevenlabs_voice_id, language_code, similarity, stability, style, speed) values
  ('Vedantu Female',  'vedantu_female',  '21m00Tcm4TlvDq8ikWAM', null, 0.80, 0.55, 0.15, 1.00), -- Rachel
  ('Vedantu Male',    'vedantu_male',    'pNInz6obpgDQGcFmaJgB', null, 0.80, 0.55, 0.15, 1.00), -- Adam
  ('Teacher Female',  'teacher_female',  'EXAVITQu4vr4xnSDxMaL', null, 0.75, 0.65, 0.10, 0.95), -- Bella
  ('Teacher Male',    'teacher_male',    'VR6AewLTigWG4xSOukaG', null, 0.75, 0.65, 0.10, 0.95), -- Arnold
  ('Parent Female',   'parent_female',   'AZnzlk1XvdvUeBnXmlld', null, 0.75, 0.60, 0.20, 0.95), -- Domi
  ('Parent Male',     'parent_male',     'TxGEqnHWrfWFTfGW9XjX', null, 0.75, 0.60, 0.20, 0.95), -- Josh
  ('Friendly',        'friendly',        'ErXwobaYiN019PkySvjV', null, 0.70, 0.45, 0.35, 1.05), -- Antoni
  ('Professional',    'professional',    'MF3mGyEYCl7XYWbV9V6O', null, 0.85, 0.70, 0.05, 1.00); -- Elli
