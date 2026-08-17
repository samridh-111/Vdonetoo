# Automation Hub

Internal tooling for batch IVR (Interactive Voice Response) audio generation and creative automation. Upload a script sheet, pick voices and languages, and get a ZIP of production-ready MP3s — no manual studio work.

---

## Table of Contents

- [What this is](#what-this-is)
- [Architecture overview](#architecture-overview)
- [IVR Automation — how it works](#ivr-automation--how-it-works)
- [Script sheet format](#script-sheet-format)
- [Translation modes](#translation-modes)
- [Local development](#local-development)
- [Environment variables](#environment-variables)
- [Deployment](#deployment)
- [Next steps — Aspect Ratio Creator](#next-steps--aspect-ratio-creator)

---

## What this is

**Automation Hub** is a Next.js + FastAPI internal tool with two planned modules:

| Module | Status | Description |
|---|---|---|
| **IVR Automation** | ✅ Built | Batch TTS audio generation from script sheets. Multi-language, multi-voice, Celery-backed. |
| **Creative Automation / Aspect Ratio Creator** | 🔲 Next | Auto-generate platform-specific creative variants from a master copy. See [next steps](#next-steps--aspect-ratio-creator). |

---

## Architecture overview

```
┌──────────────────────────────────────┐
│            Next.js frontend          │  :3000
│  (upload → preview → status → DL)   │
└────────────────┬─────────────────────┘
                 │ REST + WebSocket
┌────────────────▼─────────────────────┐
│          FastAPI backend             │  :8000
│  /api/v1/upload  /api/v1/batch       │
│  /ws/batch/{id}  /api/v1/voices      │
└──────┬─────────────────┬─────────────┘
       │ DB (asyncpg)    │ Celery tasks (chord)
┌──────▼──────┐   ┌──────▼──────────────────────┐
│  Supabase   │   │  Celery worker + beat        │
│  Postgres   │   │  • prepare_script            │
│  Storage    │   │    (translate per language)  │
│  (MP3s/ZIP) │   │  • generate_audio_for_job    │
└─────────────┘   │    (ElevenLabs TTS + upload) │
                  │  • build_zip_and_finalize    │
┌─────────────┐   │    (ZIP → Supabase → notify) │
│    Redis    │◄──┤                              │
│  broker +   │   │  Celery-beat: rate-limit     │
│  rate limiter│  │  token refill (every 1s)     │
└─────────────┘   └──────────────────────────────┘
```

**Key technology choices:**

- **FastAPI** — async API, Pydantic v2 schemas, SQLAlchemy 2 async ORM
- **Celery + Redis** — task queue; `chord` primitive fans out all scripts/jobs in parallel then converges
- **ElevenLabs** — TTS provider (configurable voice, stability, similarity, style, speed)
- **Translation** — pluggable: `openai` (gpt-4o-mini), `gemini` (gemini-flash), or `mymemory` (free/no billing)
- **Supabase** — Postgres DB + object storage for MP3s and batch ZIPs
- **Rate limiter** — token-bucket in Redis; Celery-beat refills every second so ElevenLabs and translation API limits are respected without blocking workers

---

## IVR Automation — how it works

### 1. Upload

Hit `POST /api/v1/upload/file` (or `/upload/url` for a Google Sheet). The service:

1. Parses `.xlsx` or `.csv` into a DataFrame.
2. **Fuzzy-matches column headers** — columns named `Script`, `text`, `dialogue`, `content`, etc. all resolve to the script column. Same for `ID`, `Language`, `Voice`, `Notes`.
3. Runs per-row validation (empty script = invalid).
4. Runs **language detection** (`langdetect`) on each script text.
5. **Stashes** parsed rows in Redis under a short-lived token (30 min TTL) — nothing hits the DB yet so the user can still tweak settings in the preview UI.
6. Returns `{ upload_token, rows[], column_map, stats }`.

### 2. Preview & configure

The frontend shows the batch preview table. The user picks:

- **Translation mode** — keep original / translate selected / translate everything / generate multiple
- **Target languages** — checked against the active-language registry in Postgres
- **Translation provider** — OpenAI / Gemini / MyMemory
- **Voice map** — per-language ElevenLabs voice assignment
- **Concurrency limit** — cap on parallel audio jobs

`POST /api/v1/batch/create` exchanges the upload token for a real batch row in Postgres (status `draft`) plus one `scripts` row per uploaded line.

`GET /api/v1/batch/estimate?script_count=N&language_count=M` returns a wall-clock estimate using the historical average generation time from completed audio files (falls back to a ~4 s/job constant until enough data exists).

### 3. Batch pipeline

`POST /api/v1/batch/{id}/start` flips status to `queued` and fires `orchestrate_batch.delay(batch_id)`.

```
orchestrate_batch
  └── chord(prepare_script × N scripts)
        └── dispatch_audio_generation
              └── chord(generate_audio_for_job × M jobs)
                    └── build_zip_and_finalize
```

**`prepare_script`** (per script, parallel):
- Detects source language, resolves target language list per translation mode
- For each target language: calls translation provider (skips if same language), resolves ElevenLabs voice, creates a `jobs` row (`stage=queued`)
- Retries up to 3× on transient errors; translation failures for one language don't abort the others

**`generate_audio_for_job`** (per job, parallel, rate-limited):
- Tries to acquire a token from the Redis ElevenLabs bucket; requeues if empty (no failure count increment)
- Calls ElevenLabs, streams MP3 bytes, uploads to Supabase Storage at `batches/{batch_id}/{lang}/{job_id}.mp3`
- Records duration (`mutagen`) and generation time; increments batch counters
- 3-attempt failure budget tracked in DB (not Celery's retry counter, which the rate-limit path also increments)

**`build_zip_and_finalize`**:
- Recomputes `completed_jobs` / `failed_jobs` from DB (source of truth, not counters)
- Builds ZIP — `metadata.csv`, `logs.txt`, and all MP3s — uploads to Supabase
- Updates batch `status → completed | failed` **after** ZIP is uploaded to avoid "ZIP not ready" races
- Publishes `batch_completed` / `batch_failed` over WebSocket

**Real-time updates** — the frontend subscribes to `WS /ws/batch/{id}`. Every stage change (`translating → generating → uploading → completed`) publishes a structured event over Redis pub/sub to that socket.

**Cancellation** — `POST /api/v1/batch/{id}/cancel` writes a cancellation key to Redis. Workers check `is_batch_cancelled()` before each expensive step and bail out cleanly.

### 4. Download

Once `status=completed`, `GET /api/v1/batch/{id}/download` returns a short-lived signed URL to the Supabase-stored ZIP.

---

## Script sheet format

Download the template from the UI. Supported columns (case-insensitive, fuzzy-matched):

| Column | Required | Notes |
|---|---|---|
| `Script` / `Text` / `Content` | ✅ | The IVR script text |
| `ID` / `Script ID` | — | External reference ID, appears in ZIP filenames |
| `Title` / `Name` | — | Human label for the preview table |
| `Language` / `Lang` | — | Hint for source language (auto-detected if absent) |
| `Voice` / `Voice Preset` | — | ElevenLabs voice name hint; overrides the default voice map |
| `Notes` / `Comments` | — | Stored in metadata, not synthesised |

Rows with an empty Script column are marked `invalid` at parse time and skipped by the pipeline (still visible in the preview table).

---

## Translation modes

| Mode | Behaviour |
|---|---|
| `keep_original` | Only generate audio in the detected source language. No translation calls. |
| `translate_selected` | Generate audio for the explicitly listed target languages (+ source). |
| `translate_everything` | Generate audio for every active language in the registry. |
| `generate_multiple` | Alias of `translate_selected` — fan out to configured languages. |

---

## Local development

**Prerequisites:** Docker, Python 3.12+, Node 20+.

```bash
# 1. Clone and copy env
cp .env.example .env
# fill in SUPABASE_*, ELEVENLABS_API_KEY, OPENAI_API_KEY (or GEMINI_API_KEY)

# 2. Start Redis (and optionally all services via Docker Compose)
docker compose up redis -d

# 3. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 4. Celery worker (separate terminal)
celery -A app.core.celery_app.celery_app worker --loglevel=info -c 4

# 5. Celery beat (separate terminal — needed for rate-limit token refill)
celery -A app.core.celery_app.celery_app beat --loglevel=info

# 6. Frontend
cd frontend
npm install
npm run dev        # :3000
```

**Full stack via Docker Compose:**
```bash
docker compose up --build
```
Services: `redis :6379`, `backend :8000`, `worker`, `worker-beat`, `frontend :3000`.

**Tests:**
```bash
cd backend
pytest --cov=app
```

---

## Environment variables

See [`.env.example`](.env.example) for the full annotated list. Key ones:

| Variable | Default | Notes |
|---|---|---|
| `SUPABASE_URL` | — | Your project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Service role (not anon) key |
| `SUPABASE_DB_URL` | — | `postgresql+asyncpg://...` |
| `SUPABASE_AUDIO_BUCKET` | `ivr-audio` | Bucket for individual MP3s |
| `SUPABASE_BATCH_BUCKET` | `ivr-batches` | Bucket for batch ZIPs |
| `ELEVENLABS_API_KEY` | — | |
| `ELEVENLABS_MAX_CONCURRENCY` | `8` | Parallel TTS calls |
| `ELEVENLABS_RATE_PER_MIN` | `60` | Token-bucket rate cap |
| `TRANSLATION_PROVIDER` | `openai` | `openai` \| `gemini` \| `mymemory` |
| `OPENAI_API_KEY` | — | Used when `TRANSLATION_PROVIDER=openai` |
| `TRANSLATION_MAX_CONCURRENCY` | `2` | Lower on free-tier keys |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Baked into Next.js at build time |

> **Never commit `.env`.** It is in `.gitignore`. Use `.env.example` as the reference.

---

## Deployment

The [`render.yaml`](render.yaml) defines a Phase 1 Render deployment (not yet validated against a live account):

| Service | Type | Notes |
|---|---|---|
| `ivr-automation-redis` | Redis (starter) | Shared broker/result-backend |
| `ivr-automation-backend` | Web (Docker) | FastAPI on `backend/Dockerfile` |
| `ivr-automation-worker` | Worker (Docker) | Celery worker on `Dockerfile.worker` |
| `ivr-automation-beat` | Worker (Docker) | Celery beat — rate-limit token refill |

Frontend is deployed separately via **Vercel** ([`vercel.json`](vercel.json)). `NEXT_PUBLIC_*` vars must be set as Vercel environment variables (they're inlined at build time).

**Before deploying:**
1. Verify service plan names match your Render account tier.
2. Set all `sync: false` env vars in the Render dashboard.
3. Run Supabase migrations (Alembic — `alembic upgrade head` from `backend/`).
4. Create the Supabase storage buckets (`ivr-audio`, `ivr-batches`) with appropriate RLS policies.

---

## Next steps — Aspect Ratio Creator

The **Aspect Ratio Creator** is the next module in Automation Hub. The goal: given a **master creative** (a video/image ad), automatically produce correctly-cropped and reframed variants for every platform and placement (e.g. 16:9 → 9:16 → 1:1 → 4:5).

### Concept

A creative team produces one master copy — the canonical, highest-quality version of an ad. Every downstream deliverable (Stories, Reels, Feed, YouTube, Display) is derived from it. Today that derivation is manual. The Aspect Ratio Creator automates it.

### Proposed flow

```
1. Upload master creative
   └── single video (MP4) or image (PNG/JPG/WebP)

2. Configure output targets
   └── select platform presets (or enter custom WxH + safe zone)
       presets: 16:9  9:16  1:1  4:5  1.91:1  2:3  ...

3. Smart reframe (per target)
   └── subject detection → crop to keep subject in frame
       fallback: centre-crop

4. Batch export
   └── all variants in a ZIP  (or  push directly to DAM/asset library)
```

### What needs to be built

| Area | Work |
|---|---|
| **DB schema** | `creative_batches`, `creative_assets` tables (mirrors `batches`/`scripts`/`jobs` pattern) |
| **Upload service** | Accept video + image; validate MIME type; store master in Supabase Storage; stash token in Redis (same 30 min TTL pattern) |
| **Reframe engine** | FFmpeg crop + scale per target ratio. Subject detection via OpenCV face/body or Vision API (Gemini Vision / GPT-4o) to find the primary subject bounding box |
| **Platform preset registry** | Postgres table of named presets (name, width, height, safe-zone insets); seeded via Alembic migration |
| **Celery task graph** | `orchestrate_creative_batch → chord(reframe_asset × N targets) → build_creative_zip` — same chord-callback structure as IVR |
| **Frontend page** | `/creative-automation` route (nav item already exists in the sidebar). Upload master → target picker → live progress → download |
| **API routes** | `POST /api/v1/creative/upload`, `POST /api/v1/creative/batch/create`, `GET /api/v1/creative/batch/{id}/status`, `GET /api/v1/creative/batch/{id}/download` |
| **Real-time progress** | Reuse WebSocket infrastructure — publish `reframe_progress` events per job |

### Suggested implementation order

1. **Migrations** — add `creative_batches` and `creative_assets` tables.
2. **Upload + stash** — `CreativeUploadService`; validate MIME, upload master to `creative-masters` bucket, stash parsed config in Redis.
3. **Preset registry** — seed standard platform presets; expose `GET /api/v1/creative/presets`.
4. **Reframe worker** — spike FFmpeg crop/scale in a standalone script first; wrap in a Celery task once the math is confirmed.
5. **Subject detection (optional MVP gate)** — start with centre-crop as the default; Vision-API bounding box as a toggle.
6. **ZIP + finalize** — reuse `ZipService` pattern from IVR; include a `manifest.json` mapping each variant to its preset.
7. **Frontend** — wire up the existing "Creative Automation" nav link to the new page.

### Open questions / decisions needed

- **Reframe method**: pure FFmpeg centre-crop (fast, dumb) vs. Vision API subject detection (smarter, costs API calls) vs. user-drawn crop box in the UI?
- **Supported input formats**: MP4 only to start, or also MOV/AVI? Images-only as a simpler MVP?
- **Output format**: always MP4 (H.264) + original image format, or configurable per-preset?
- **Safe zones**: enforce platform-specific text-safe zones (e.g. TikTok bottom 20%) as overlaid guides, or as hard exclusion zones during crop?
- **DAM integration**: push to Bynder / Brandfolder / Google Drive, or ZIP download only for now?
- **Output naming convention**: `{master_name}_{width}x{height}.mp4` or keyed by platform preset name (e.g. `{master_name}_stories.mp4`)?
