# Evidence — frontend

Job matching that shows its working. This is the Next.js frontend for the hackathon build.
It runs entirely on fixture data today; the FastAPI backend plugs in through one file.

## Run it

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build + type check
npm run lint
```

Copy `.env.example` to `.env.local`. Leave `NEXT_PUBLIC_API_BASE_URL` empty to keep using fixtures.

## Run the resume API

From `backend/`, install the Python dependencies and start FastAPI:

```bash
python -m pip install -r requirements.txt
uvicorn src.app.main:app --reload
```

The upload endpoint is `POST http://localhost:8000/resumes` with a multipart
form field named `file`. It accepts PDF files up to 10 MB, saves the original
under `backend/storage/original_resumes/`, extracts resume text, and stores the
person, resume, experience, education, projects, and skills in the local SQLite
database. A successful response contains `resumeId` and the parsed resume.

When `BEDROCK_AGENT_ID` is configured, the extracted text is sent to the
Bedrock Agent Runtime using `BEDROCK_AGENT_ALIAS_ID` and `AWS_REGION`. Without
that setting, the local parser is used as a development fallback. AWS
credentials are read through the standard boto3 credential chain.

## Screens

| Route       | Stage           | Interactive parts                                   |
| ----------- | --------------- | --------------------------------------------------- |
| `/`         | Upload resume   | Drop zone / file picker → `/facts`                  |
| `/facts`    | Check the facts | Remove a fact locally, Edit is a placeholder        |
| `/profile`  | Three questions | Segmented answers, saves then → `/discover`         |
| `/discover` | Find jobs       | "Close to" vs "Browse" mode, job rows → `/match`    |
| `/match`    | Match report    | Click a requirement to see its proof line           |
| `/pass`     | Work pass check | Static COMPASS breakdown                            |
| `/act`      | Take action     | Tabs: tailor (approve diffs), learn, prep, reach    |
| `/watch`    | Overnight watch | On/off toggle                                       |
| `/track`    | Track progress  | Static table                                        |

`/match`, `/pass` and `/act` accept `?job=<id>`. Without it they fall back to the fixture job.

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
  data.ts             fixture data (never import from components; go through api.ts)
  api.ts              BACKEND PLACEHOLDER — the only file the UI talks to for data
  routes.ts           tiny URL helpers
```

## For the backend team

Everything the UI needs is a function in [lib/api.ts](lib/api.ts). Each one has a `TODO(backend)`
comment naming the suggested endpoint. Replace the fixture return with a call through the `request()`
helper in the same file, keep the return types in [lib/types.ts](lib/types.ts), and no screen
needs to change.

Suggested FastAPI endpoint map:

```
POST /resumes                     uploadResume
GET  /resumes/:id/facts           fetchFacts
GET  /profile/questions           fetchProfileQuestions
PUT  /profile                     saveProfile
GET  /jobs?mode=close|browse      fetchJobs
GET  /jobs/unlocks                fetchUnlocks
GET  /jobs/summary                fetchDiscoverSummary
GET  /jobs/:id/match              fetchMatchReport
GET  /jobs/:id/compass            fetchCompassReport
GET  /jobs/:id/actions            fetchActionCenter
GET  /watch                       fetchWatchFeed
PUT  /watch                       setWatchEnabled
GET  /applications                fetchTracker
GET  /session                     fetchSessionSummary
```

Not yet represented in the API layer but referenced by UI placeholders: editing/removing a fact,
downloading the tailored resume, "make it shorter / rewrite" on the outreach draft, and opening
a single application from the tracker.
