-- Shared by every automation module (IVR now; Creative Automation, Asset
-- Library, Localization, Campaign Automation later) -- not IVR-specific.
create table projects (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  module text not null default 'ivr_automation',
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index ix_projects_module on projects(module);
