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
