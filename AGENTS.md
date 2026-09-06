<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Evidence — hackathon project agent notes

Next.js frontend (`app/`, `lib/`, `components/`) + FastAPI/SQLite backend (`backend/`). Full
setup, endpoint reference, and known limitations are in [README.md](README.md) — read that first.

## Running both servers

```bash
# backend, from backend/
python -m pip install -r requirements.txt
uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload --env-file ../.env

# frontend, from repo root
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Key facts for agents working in this repo

- **The API contract lives in `lib/types.ts`.** Every backend response shape must match it
  field-for-field (checked by the frontend at compile time via TypeScript, not by the backend).
- **`lib/api.ts`** is the only file the frontend talks to for data. It currently calls the real
  backend for every screen except `/act` (still fixture data — see README's Known Limitations).
- **Backend endpoints accepting `resume_id`** must 404 on an explicit-but-nonexistent id, and
  fall back to the most recently uploaded resume when the param is omitted entirely. This pattern
  is applied consistently across `/jobs`, `/jobs/summary`, `/jobs/unlocks`, `/watch`,
  `/applications`, and `/session` — keep it consistent if you add a new one.
- **`backend/tests/` has no `__init__.py`.** Run the suite with
  `python -m unittest discover -s tests -v`, not `python -m unittest tests.test_X -v` (the latter
  fails with `ModuleNotFoundError` — not a bug).
- **Bedrock scoring requires real AWS credentials** in `.env` at the repo root. Without them,
  multi-job endpoints (`/jobs`, `/jobs/summary`, `/jobs/unlocks`) degrade every job to score `0`
  rather than failing; single-job endpoints (`/jobs/:id/match`, `/jobs/:id/requirements`,
  `/jobs/:id/learning-gaps`) return `503`.
- **Auth is explicitly out of scope** for this hackathon MVP — do not add login/session auth
  unless asked.
- End-to-end verification screenshots (real resume, live backend + frontend) are in
  [`.claude/screenshots/`](.claude/screenshots/).
