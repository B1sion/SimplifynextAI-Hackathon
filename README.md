# Evidence — job matching that shows its working

A Next.js frontend + FastAPI/SQLite backend built for the SimplifynextAI hackathon. Upload a
resume, get parsed facts with source lines, match against stored jobs, and track applications —
all backed by a real API, not fixture data.

**Status:** frontend and backend are fully wired for every screen except `/act` (recruiter
outreach / interview prep — owned separately, still on fixture data). See
[Known limitations](#known-limitations) below.

## Quick start

Two servers, two terminals, from the repo root.

**1. Backend (FastAPI + SQLite), from `backend/`:**

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload --env-file ../.env
```

**2. Frontend (Next.js), from the repo root:**

```bash
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev   # http://localhost:3000
```

Copy `.env.example` to `.env` at the repo root and fill in AWS credentials (see
[Environment variables](#environment-variables)) before starting the backend — the app boots
without them, but resume scoring calls to Bedrock will fail until they're set.

## Environment variables

Set these in `.env` at the repo root (backend reads it via `--env-file ../.env`):

| Variable                  | Required        | Purpose                                                              |
| -------------------------- | ---------------- | ---------------------------------------------------------------------- |
| `AWS_REGION`               | for scoring      | Bedrock region, e.g. `us-east-1`                                       |
| `AWS_ACCESS_KEY_ID`        | for scoring      | Standard boto3 credential chain                                        |
| `AWS_SECRET_ACCESS_KEY`    | for scoring      | Standard boto3 credential chain                                        |
| `AWS_SESSION_TOKEN`        | for scoring      | Only needed for temporary/STS credentials                              |
| `BEDROCK_MODEL_ID`         | for scoring      | Model used for resume ↔ job evaluation (`evaluate_resume`)             |
| `CORS_ALLOWED_ORIGINS`     | no               | Comma-separated allowed origins; defaults to `http://localhost:3000`   |
| `NEXT_PUBLIC_API_BASE_URL` | yes (frontend)   | Set to the backend URL so the UI stops using fixture data              |

Without valid AWS credentials, endpoints that call Bedrock (`/jobs`, `/jobs/summary`,
`/jobs/unlocks`, `/jobs/:id/match`, `/jobs/:id/requirements`, `/jobs/:id/learning-gaps`) either
degrade every job to a `0` score (the multi-job list endpoints, which isolate per-job failures)
or return `503` (the single-job endpoints). Everything else works with no AWS setup at all.

## Screens

| Route       | Stage           | Backed by                                                       |
| ----------- | --------------- | ------------------------------------------------------------------ |
| `/`         | Upload resume   | `POST /resumes` (multipart PDF, ≤10 MB)                            |
| `/facts`    | Check the facts | `GET /resumes/:id/facts`                                           |
| `/profile`  | Three questions | `GET /profile/questions`, `PUT /profile`                            |
| `/discover` | Find jobs       | `GET /jobs`, `GET /jobs/summary`, `GET /jobs/unlocks`                |
| `/match`    | Match report    | `GET /jobs/:id/match`                                               |
| `/pass`     | Work pass check | `GET /jobs/:id/compass` (fixed stub — see limitations)               |
| `/act`      | Take action     | **Not wired** — fixture data (`lib/api.ts::fetchActionCenter`)      |
| `/watch`    | Overnight watch | `GET /watch`, `PUT /watch`                                          |
| `/track`    | Track progress  | `GET /applications`                                                 |

`/match`, `/pass` and `/act` accept `?job=<id>`. Without it they fall back to the fixture job.

## Backend API reference

All routes live in `backend/src/app/main.py`. Base URL: `http://localhost:8000`.

```
GET  /health                              liveness check

POST /resumes                             upload a PDF resume (multipart `file`), returns {resumeId, resume}
GET  /resumes/:id/facts                   parsed facts grouped by section, with source lines

GET  /profile/questions                   static question catalog (mirrors lib/data.ts)
PUT  /profile                             {"answers": {questionId: optionIndex}} -> 204

GET  /jobs?resume_id=                     jobs ranked by fewest missing requirements
GET  /jobs/summary?resume_id=             verdict counts (canApply / mightNotQualify / cannotApply)
GET  /jobs/unlocks?resume_id=             top missing skills ranked by how many roles they'd open
GET  /jobs/:id/match?resume_id=           full match report: score, verdict, requirements, workPass stub
GET  /jobs/:id/compass                    fixed COMPASS/work-pass stub (not real scoring yet)
GET  /jobs/:id/requirements?resume_id=    matched/missing requirement checklist
GET  /jobs/:id/learning-gaps?resume_id=   skill gaps + other roles that would close them
POST /jobs/:id/optimize                   kick off a resume-tailoring run for a job

GET  /watch?resume_id=                    watch feed (real `enabled` flag; scan history is stubbed)
PUT  /watch?resume_id=                    {"enabled": bool} -> 204

GET  /applications?resume_id=             application tracker (real, empty until a future "mark as applied" UI exists)
GET  /session?resume_id=                  candidate name, confirmed-fact count, watch/claims placeholders

GET  /optimization-runs/:id                     a tailoring run's status
GET  /optimization-runs/:id/versions            every generated resume version for a run
GET  /optimization-runs/:id/resume.pdf          download a generated PDF
```

Every endpoint accepting `resume_id` falls back to the most recently uploaded resume when it's
omitted, and returns `404` if an explicit `resume_id` doesn't exist.

## Known limitations

Documented, deliberate trade-offs made to hit the hackathon deadline — not bugs:

- **`/act` (recruiter outreach, interview prep, resume diffs)** — owned by another contributor;
  still serves fixture data from `lib/data.ts`.
- **COMPASS / Employment Pass scoring** (`GET /jobs/:id/compass`, the `workPass` field on
  `GET /jobs/:id/match`) — fixed stub values. The `compass_reports` table exists in the schema
  so this can be swapped for real scoring without a migration.
- **Overnight watch** — the on/off toggle is real and persisted (`watch_settings` table); there is
  no scheduler yet, so the event feed is always empty.
- **Applications tracker** — real and persisted (`applications` table), but always empty; no UI
  action exists yet to call `create_application`.
- **`claimsBlocked`** (`GET /session`) — always `0`; no table persists validation-report data yet.
- **DOCX resume upload** — PDF only; no `python-docx`-equivalent dependency is installed.
- **Auth** — explicitly out of scope for this MVP; there is no login, and `resume_id` is a
  guessable sequential integer.

## Screenshots

End-to-end verification screenshots (real uploaded resume, live backend + frontend, captured with
Playwright) live in [`.claude/screenshots/`](.claude/screenshots/):

| File              | Screen                                           |
| ------------------ | --------------------------------------------------- |
| `01-upload.png`   | `/` — upload resume                                |
| `02-facts.png`    | `/facts` — parsed facts from a real PDF            |
| `03-profile.png`  | `/profile` — three questions                        |
| `04-discover.png` | `/discover` — job list ranked against the resume    |
| `05-match.png`    | `/match?job=` — match report                        |
| `06-pass.png`     | `/pass?job=` — work pass check (stub)                |
| `07-watch.png`    | `/watch` — overnight watch toggle                    |
| `08-track.png`    | `/track` — application tracker                       |
| `09-act.png`      | `/act?job=` — action center (fixture data)          |

## Layout

```
app/                  one folder per route; pages are Server Components that call lib/api
  layout.tsx          root shell: fonts, left rail, canvas
  globals.css         Tailwind import + design tokens + the shared component classes
components/
  ui.tsx              Card, Tag, ButtonLink, PageHeader, SectionHead …
  rail.tsx            left-hand step navigation (client, highlights current route)
  screens/            client components for the interactive bits of each screen
lib/
  types.ts            the data contract the screens render
  data.ts             fixture data (still used by /act; imported as a fallback elsewhere)
  api.ts              the only file the UI talks to for data — swap NEXT_PUBLIC_API_BASE_URL to point at the backend
  routes.ts           tiny URL helpers

backend/
  src/app/main.py             FastAPI routes (all endpoints listed above)
  src/Tools/                  DB-facing CRUD modules (resumes, jobs, profile, watch, applications, ...)
  src/services/
    presenters.py             shapes backend rows into the exact JSON the frontend expects
    job_ranking.py             ranks stored jobs against a resume, isolating per-job Bedrock failures
  src/agents/resume_agents/    resume parsing, job parsing, ATS evaluation, Bedrock client
  database/database.py        SQLite schema + connection helper
  tests/                      unittest suite — run with `python -m unittest discover -s tests -v`
```

## Testing

```bash
cd backend
python -m unittest discover -s tests -v
```

(`python -m unittest tests.test_api -v` fails with `ModuleNotFoundError` — there's no
`tests/__init__.py` — use `discover` as shown above.)

```bash
npm run build   # type check + production build
npm run lint
```
