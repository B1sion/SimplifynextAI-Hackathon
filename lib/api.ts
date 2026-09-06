/**
 * BACKEND PLACEHOLDER LAYER
 * ─────────────────────────
 * This is the only file the UI talks to for data. Every function currently
 * resolves fixture data from ./data.ts so the frontend can be built and demoed
 * without a backend.
 *
 * For the backend team: replace each function body with a real call (see the
 * TODO on each one). Keep the signatures and the return types in ./types.ts —
 * the screens depend on them. Set NEXT_PUBLIC_API_BASE_URL in .env.local once
 * an API exists.
 *
 * Suggested endpoint map (not implemented anywhere yet):
 *   POST /resumes                     uploadResume
 *   GET  /resumes/:id/facts           fetchFacts
 *   GET  /profile/questions           fetchProfileQuestions
 *   PUT  /profile                     saveProfile
 *   GET  /jobs?mode=close|browse      fetchJobs
 *   GET  /jobs/unlocks                fetchUnlocks
 *   GET  /jobs/summary                fetchDiscoverSummary
 *   GET  /jobs/:id/match              fetchMatchReport
 *   GET  /jobs/:id/compass            fetchCompassReport
 *   GET  /jobs/:id/actions            fetchActionCenter
 *   GET  /watch                       fetchWatchFeed
 *   PUT  /watch                       setWatchEnabled
 *   GET  /applications                fetchTracker
 *   GET  /session                     fetchSessionSummary
 */

import {
  ACTION_CENTER,
  COMPASS_REPORT,
  DISCOVER_SUMMARY,
  FACTS,
  JOBS,
  MATCH_REPORT,
  PROFILE_QUESTIONS,
  SESSION_SUMMARY,
  STAGES,
  TRACKER,
  UNLOCKS,
  WATCH_FEED,
} from "./data";
import type {
  ActionCenter,
  CompassReport,
  DiscoverSummary,
  FactGroup,
  InterviewPrep,
  Job,
  MatchReport,
  ProfileQuestion,
  SessionSummary,
  SkillUnlock,
  StageGroup,
  Tracker,
  WatchFeed,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

/** Job the per-job screens fall back to when no `?job=` param is present. */
export const DEFAULT_JOB_ID = MATCH_REPORT.jobId;

/**
 * Thin fetch wrapper for the backend team. Not used by any function below yet;
 * swap a fixture return for `return request<T>("/path")` when the endpoint exists.
 */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not set; the UI is running on fixture data.");
  }
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed with ${res.status}`);
  }
  return (await res.json()) as T;
}

/* --------------------------------- session --------------------------------- */

export async function fetchStages(): Promise<StageGroup[]> {
  // Static navigation config; unlikely to need a backend.
  return STAGES;
}

export async function fetchSessionSummary(): Promise<SessionSummary> {
  // TODO(backend): GET /session — candidate name, confirmed fact count, last watch run.
  return SESSION_SUMMARY;
}

/* ---------------------------------- setup ---------------------------------- */

export async function uploadResume(file: File): Promise<{ resumeId: string }> {
  // TODO(backend): POST /resumes (multipart). Returns the id used by fetchFacts.
  void file;
  return { resumeId: "mock-resume" };
}

export async function fetchFacts(): Promise<FactGroup[]> {
  // TODO(backend): GET /resumes/:id/facts — parsed facts with source lines.
  return FACTS;
}

export async function fetchProfileQuestions(): Promise<ProfileQuestion[]> {
  // TODO(backend): GET /profile/questions (or keep static if the questions never change).
  return PROFILE_QUESTIONS;
}

export async function saveProfile(answers: Record<string, number>): Promise<void> {
  // TODO(backend): PUT /profile — answers keyed by question id, value = option index.
  void answers;
}

/* --------------------------------- discover -------------------------------- */

export async function fetchJobs(mode: "close" | "browse" = "close"): Promise<Job[]> {
  // TODO(backend): GET /jobs?mode=... — "close" ranks by fewest missing requirements.
  if (mode === "browse") {
    return [...JOBS].sort((a, b) => a.title.localeCompare(b.title));
  }
  return JOBS;
}

export async function fetchUnlocks(): Promise<SkillUnlock[]> {
  // TODO(backend): GET /jobs/unlocks — skills ranked by how many roles they open.
  return UNLOCKS;
}

export async function fetchDiscoverSummary(): Promise<DiscoverSummary> {
  // TODO(backend): GET /jobs/summary — verdict counts across all open roles.
  return DISCOVER_SUMMARY;
}

/* ------------------------------ per-job reports ---------------------------- */

export async function fetchMatchReport(jobId: string = DEFAULT_JOB_ID): Promise<MatchReport> {
  // TODO(backend): GET /jobs/:id/match
  void jobId;
  return MATCH_REPORT;
}

export async function fetchCompassReport(jobId: string = DEFAULT_JOB_ID): Promise<CompassReport> {
  // TODO(backend): GET /jobs/:id/compass
  void jobId;
  return COMPASS_REPORT;
}

export async function fetchActionCenter(jobId: string = DEFAULT_JOB_ID): Promise<ActionCenter> {
  // TODO(backend): GET /jobs/:id/actions — diffs, skill gaps, interview prep, contacts, draft.
  void jobId;
  return ACTION_CENTER;
}

export async function fetchInterviewQuestions(jobId: string = DEFAULT_JOB_ID): Promise<InterviewPrep> {
  // Backend falls back to the latest resume when no resume_id is supplied.
  // Known limitation: real mode needs an int job id in ?job= (backend SQLite ids);
  // fixture slugs like "shopee-product-analyst" do not resolve.
  return request<InterviewPrep>(`/jobs/${jobId}/interview-questions`);
}

/* ---------------------------------- watch ---------------------------------- */

export async function fetchWatchFeed(): Promise<WatchFeed> {
  // TODO(backend): GET /watch — last overnight run and its change events.
  return WATCH_FEED;
}

export async function setWatchEnabled(enabled: boolean): Promise<void> {
  // TODO(backend): PUT /watch { enabled }
  void enabled;
}

/* ---------------------------------- track ---------------------------------- */

export async function fetchTracker(): Promise<Tracker> {
  // TODO(backend): GET /applications — metrics plus the list of sent applications.
  return TRACKER;
}
