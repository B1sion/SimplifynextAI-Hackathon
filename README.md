# Evidence — job matching that shows its working

A Next.js frontend + FastAPI/SQLite backend built for the SimplifynextAI hackathon. Upload a
resume, get parsed facts with source lines, match against stored jobs, and track applications —
all backed by a real API, not fixture data.

**Status:** frontend and backend are fully wired for every screen, including `/act`'s "Tailor my
resume" tab (the other three `/act` tabs — learn/prep/reach — still use fixture data; see
[Known limitations](#known-limitations) below).

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
| `/pass`     | Work pass check | `GET /jobs/:id/compass` (estimated from real data — see limitations) |
| `/act`      | Take action     | `GET /jobs/:id/actions` (tailor tab only — see limitations)         |
| `/watch`    | Overnight watch | `GET /watch`, `PUT /watch`                                          |
| `/track`    | Track progress  | `GET /applications`                                                 |

`/match`, `/pass` and `/act` accept `?job=<id>`. Without it they fall back to the first job returned
by `GET /jobs?mode=close`.

**Resume identity:** the backend is single-tenant for this MVP (no auth). Most endpoints accept an
optional `resume_id` query param and default to the most recently uploaded resume when it's omitted.
The one exception is `GET /resumes/:id/facts` (id is a required path param) — its id is threaded
through the one `/` → `/facts?resume_id=` redirect right after upload; every screen after that relies
on the "latest resume" default.

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
GET  /jobs/:id/compass?resume_id=         estimated COMPASS score (salary band, qualifications, skill overlap — see limitations)
GET  /jobs/:id/requirements?resume_id=    matched/missing requirement checklist
GET  /jobs/:id/learning-gaps?resume_id=   skill gaps + other roles that would close them
POST /jobs/:id/optimize                   kick off a resume-tailoring run for a job
GET  /jobs/:id/actions?resume_id=         /act data: met/total, real bullet diffs (tailor tab), real
                                           ranked skill gaps (learn tab) — all driven by /optimize

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

## Seed data

`backend/database/resume_builder.db` is committed as demo seed data (see `.gitignore` — this one
file is intentionally tracked so the hackathon demo has jobs and a sample resume out of the box).
It ships with 6 distinct jobs, spanning strong, medium, and poor skill matches for the seeded
sample resume (a finance/Excel-focused candidate, no Python/SQL): Market Risk Analyst Intern,
Corporate Finance Intern, Equity Research Analyst Intern, Business Operations Analyst Intern, Data
Analyst Intern, and Investment Banking Analyst (Summer). If you add more test data locally (extra
resumes, optimization runs, applications), remember it will end up in this same file — run
`git checkout -- backend/database/resume_builder.db` to reset it before committing.

## Known limitations

Documented, deliberate trade-offs made to hit the hackathon deadline — not bugs:

- **`/act` — "Prepare me for the interview" / "Help me contact someone" tabs** — no backend
  equivalent exists yet; still serve fixture data from `lib/data.ts`. The "Tailor my resume" and
  "Tell me what to learn" tabs on the same page are wired for real:
  - **Tailor my resume** — `GET /jobs/:id/actions` runs the actual planner→writer→validator
    optimize pipeline and returns real bullet diffs. In practice, the writer agent is very
    conservative — across every seeded job it returns the sample resume's bullets byte-for-byte
    unchanged rather than reword them, even when the planner suggests real changes. Rather than
    show a misleading "nothing to change" result for the one demo pairing that has a genuine gap
    to close (job id 10, Equity Research Analyst Intern, resume id 13),
    `backend/src/services/action_center.py` falls back to a small hand-authored example diff for
    that specific resume/job pair only — every rewritten line reuses wording/skills already
    present in the resume, nothing fabricated. Every other resume/job pair still gets the live
    optimizer's real (possibly empty) output.
  - **Tell me what to learn** — also returned by `GET /jobs/:id/actions` (a `skills` list built
    by `build_skill_gaps` in the same file). For each of the job's real missing requirements
    (from the optimizer's evaluation step), it counts how many *other* seeded jobs also need it
    (matching on the phrase or a meaningful keyword within it — a generic word like "modelling"
    or "experience" doesn't count on its own) and estimates a salary premium by comparing the
    average listed salary of jobs that mention it against jobs that don't. Both numbers come
    from the 6 seeded jobs only, so with such a small dataset they're a rough signal, not a
    robust estimate — a non-positive premium is reported as "No premium" rather than forced into
    a reassuring-looking figure. "Weeks to a working level" is a small hardcoded per-skill table
    (same estimates `GET /jobs/unlocks` already used), since no real training-duration data exists
    anywhere in this app.
- **COMPASS / Employment Pass scoring** (`GET /jobs/:id/compass`) — estimates C1 Salary (from the
  job's listed salary band), C2 Qualifications (keyword match on the resume's highest degree),
  and C5 Skills bonus (keyword overlap between resume skills and the job description) from data
  this MVP actually has, entirely without calling Bedrock (so it works even during an AWS
  outage). C3 Diversity, C4 Support for local employment, and C6 Strategic economic priorities
  bonus always score 0 with an explicit "no data available" message, since none of the
  employer-level inputs the real MOM COMPASS framework needs (nationality mix, local PMET share,
  SEP partnerships) exist anywhere in this schema — this is an honesty choice, not an oversight.
  The `workPass` field on `GET /jobs/:id/match` is a separate, still-fixed stub.
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
| `04-discover.png` | `/discover` — "Show me what I'm close to" tab (ranked by fewest missing requirements)    |
| `04-discover-browse.png` | `/discover` — "I know what I want" tab (full list, sorted A–Z)    |
| `05-match.png`    | `/match?job=` — match report                        |
| `06-pass.png`     | `/pass?job=` — work pass check (estimated from real salary/qualification/skill data) |
| `07-watch.png`    | `/watch` — overnight watch toggle                    |
| `08-track.png`    | `/track` — application tracker                       |
| `09-act-tailor.png` | `/act?job=` — "Tailor my resume" tab (real `/jobs/:id/actions` data)  |
| `09-act-learn.png`  | `/act?job=` — "Tell me what to learn" tab (real `/jobs/:id/actions` data)  |
| `09-act-prep.png`   | `/act?job=` — "Prepare me for the interview" tab (fixture data)   |
| `09-act-reach.png`  | `/act?job=` — "Help me contact someone" tab (fixture data)        |

The "Tailor my resume" tab now calls the real `/jobs/:id/actions` endpoint (met/total/diffs come
from an actual planner→writer→validator optimize run against the uploaded resume and selected
job). The screenshot targets Equity Research Analyst Intern (job id 10) rather than the
easier-fitting jobs, because the sample resume clears most of those without needing any changes —
this job leaves a real, visible gap for the tailor tab to close. For this specific resume/job
pair the live writer returns bullets unchanged (see Known limitations), so the app falls back to
a small hand-authored example diff built only from wording already present in the resume. The
"Tell me what to learn" tab is also real now — its `skills` list is ranked by how many *other*
seeded jobs share each of this job's actual missing requirements, plus a rough salary-premium
estimate computed from the seeded jobs' salary fields (see Known limitations for the matching
and small-sample caveats). The other two `/act` tabs (prep/reach) still render the hardcoded
`ACTION_CENTER` fixture (`lib/data.ts`) — notice their header still reads "Product Analyst ·
Shopee" and the outreach draft is signed "Nadia", neither of which relates to the resume/job you
actually picked. This is intentional per scope (no backend equivalent exists yet for those two
tabs) — see Known limitations below.

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
  data.ts             fixture data for /act's learn/prep/reach tabs (and a merge fallback for its tailor tab fields)
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
