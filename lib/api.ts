/**
 * BACKEND API LAYER
 * ─────────────────
 * This is the only file the UI talks to for data. Every function below calls
 * the real FastAPI backend (see backend/src/app/main.py) via NEXT_PUBLIC_API_BASE_URL.
 *
 * fetchActionCenter (/act) calls the real /jobs/:id/actions endpoint for the
 * "Tailor my resume" tab (met/total/diffs/blocked, driven by the real
 * planner→writer→validator optimize pipeline) and the "Tell me what to
 * learn" tab (skills, ranked by real cross-job demand + a rough salary-
 * premium estimate from the seeded jobs' salary data). The "prep"/"reach"
 * tabs and the outreach draft have no backend equivalent yet and stay on the
 * ACTION_CENTER fixture — see README "Known limitations".
 *
 * Resume identity: the backend is single-tenant for this MVP (no auth). Most
 * endpoints accept an optional `resume_id` query param and default to the most
 * recently uploaded resume when it's omitted (`get_latest_resume()` server-side).
 * The one endpoint that requires an explicit id (`/resumes/:id/facts`, since
 * it's a path param) gets it threaded through the one upload → facts redirect;
 * every other screen relies on the "latest resume" default.
 *
 * Endpoint map:
 *   POST /resumes                     uploadResume
 *   GET  /resumes/:id/facts           fetchFacts
 *   GET  /profile/questions           fetchProfileQuestions
 *   PUT  /profile                     saveProfile
 *   GET  /jobs?mode=close|browse      fetchJobs
 *   GET  /jobs/unlocks                fetchUnlocks
 *   GET  /jobs/summary                fetchDiscoverSummary
 *   GET  /jobs/:id/match              fetchMatchReport
 *   GET  /jobs/:id/compass            fetchCompassReport (estimated from real job/resume data — see README)
 *   GET  /watch                       fetchWatchFeed
 *   PUT  /watch                       setWatchEnabled
 *   GET  /applications                fetchTracker
 *   GET  /session                     fetchSessionSummary
 *   GET  /jobs/:id/actions            fetchActionCenter (tailor + learn tabs)
 */

import { ACTION_CENTER, STAGES } from "./data";
import type {
  ActionCenter,
  CompassReport,
  DiscoverSummary,
  FactGroup,
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

/**
 * Thin fetch wrapper around the FastAPI backend.
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
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

/* --------------------------------- session --------------------------------- */

export async function fetchStages(): Promise<StageGroup[]> {
  // Static navigation config; unlikely to need a backend.
  return STAGES;
}

export async function fetchSessionSummary(): Promise<SessionSummary> {
  return request<SessionSummary>("/session");
}

/* ---------------------------------- setup ---------------------------------- */

export async function uploadResume(file: File): Promise<{ resumeId: string }> {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not set; the UI is running on fixture data.");
  }
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_BASE_URL}/resumes`, { method: "POST", body });
  if (!res.ok) {
    throw new Error(`POST /resumes failed with ${res.status}`);
  }
  const data = (await res.json()) as { resumeId: string };
  return { resumeId: data.resumeId };
}

export async function fetchFacts(resumeId: string): Promise<FactGroup[]> {
  return request<FactGroup[]>(`/resumes/${encodeURIComponent(resumeId)}/facts`);
}

export async function fetchProfileQuestions(): Promise<ProfileQuestion[]> {
  return request<ProfileQuestion[]>("/profile/questions");
}

export async function saveProfile(answers: Record<string, number>): Promise<void> {
  await request<void>("/profile", { method: "PUT", body: JSON.stringify({ answers }) });
}

/* --------------------------------- discover -------------------------------- */

export async function fetchJobs(mode: "close" | "browse" = "close"): Promise<Job[]> {
  return request<Job[]>(`/jobs?mode=${mode}`);
}

export async function fetchUnlocks(): Promise<SkillUnlock[]> {
  return request<SkillUnlock[]>("/jobs/unlocks");
}

export async function fetchDiscoverSummary(): Promise<DiscoverSummary> {
  return request<DiscoverSummary>("/jobs/summary");
}

/* ------------------------------ per-job reports ---------------------------- */

/** Job the per-job screens fall back to when no `?job=` param is present. */
async function defaultJobId(): Promise<string> {
  const jobs = await fetchJobs("close");
  if (jobs.length === 0) {
    throw new Error("No jobs available to fall back to; upload a resume and try again.");
  }
  return jobs[0].id;
}

export async function fetchMatchReport(jobId?: string): Promise<MatchReport> {
  const id = jobId ?? (await defaultJobId());
  return request<MatchReport>(`/jobs/${encodeURIComponent(id)}/match`);
}

export async function fetchCompassReport(jobId?: string): Promise<CompassReport> {
  const id = jobId ?? (await defaultJobId());
  return request<CompassReport>(`/jobs/${encodeURIComponent(id)}/compass`);
}

export async function fetchActionCenter(jobId?: string): Promise<ActionCenter> {
  const id = jobId ?? (await defaultJobId());
  const real = await request<
    Pick<ActionCenter, "jobId" | "jobTitle" | "company" | "met" | "total" | "diffs" | "skills"> & {
      blocked: ActionCenter["blocked"] | null;
    }
  >(`/jobs/${encodeURIComponent(id)}/actions`);
  // "prep" / "reach" tabs and the outreach draft have no backend equivalent yet
  // (see README "Known limitations"), so those pieces of the fixture are kept
  // and merged with the real tailor + learn tab data above.
  return {
    ...ACTION_CENTER,
    ...real,
    blocked: real.blocked ?? undefined,
  };
}

/* ---------------------------------- watch ---------------------------------- */

export async function fetchWatchFeed(): Promise<WatchFeed> {
  return request<WatchFeed>("/watch");
}

export async function setWatchEnabled(enabled: boolean): Promise<void> {
  await request<void>("/watch", { method: "PUT", body: JSON.stringify({ enabled }) });
}

/* ---------------------------------- track ---------------------------------- */

export async function fetchTracker(): Promise<Tracker> {
  return request<Tracker>("/applications");
}
