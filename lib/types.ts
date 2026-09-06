/**
 * Shared domain types for the Evidence job-finder UI.
 *
 * These mirror the shapes the frontend renders today (fixture data in ./data.ts).
 * When the backend is wired up, keep these as the contract between API responses
 * and the screens — adapt on the API layer (./api.ts), not in components.
 */

/** Traffic-light verdict used across tags, badges and score chips. */
export type Verdict = "v" | "c" | "b"; // v = verified / can apply, c = caution, b = blocked

/* ---------------------------------- setup ---------------------------------- */

export interface Fact {
  /** Human-readable value we extracted, e.g. "Python — pandas, Airflow". */
  value: string;
  /** The exact resume line that proves it. */
  source: string;
  /** Where in the resume it came from, e.g. "Experience · line 14". */
  location: string;
}

export interface FactGroup {
  group: string;
  items: Fact[];
}

export interface ProfileQuestion {
  id: string;
  question: string;
  options: string[];
  /** Index into `options` that is pre-selected. */
  defaultPick: number;
}

export interface SessionSummary {
  candidateName: string;
  factsConfirmed: number;
  claimsBlocked: number;
  /** e.g. "03:18 today" */
  lastWatchRun: string;
}

/* --------------------------------- discover -------------------------------- */

export interface SkillUnlock {
  name: string;
  /** Roles that open up if the candidate learns this. */
  jobs: number;
  /** Time to a working level, e.g. "3 weeks". */
  weeks: string;
  /** 0–100, relative bar width. */
  pct: number;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  /** Requirements met out of 10. */
  score: number;
  verdict: Verdict;
  verdictLabel: string;
}

export interface DiscoverSummary {
  totalRoles: number;
  canApply: number;
  mightNotQualify: number;
  cannotApply: number;
}

/* ---------------------------------- match ---------------------------------- */

export interface AgentStatus {
  name: string;
  ok: boolean;
  detail: string;
}

export type Requirement =
  | { met: true; text: string; evidence: string; location: string }
  | { met: false; text: string; note: string };

export interface WorkPassSummary {
  points: number;
  needed: number;
  summary: string;
}

export interface MatchReport {
  jobId: string;
  jobTitle: string;
  company: string;
  location: string;
  verdict: Verdict;
  verdictLabel: string;
  agents: AgentStatus[];
  requirements: Requirement[];
  workPass: WorkPassSummary;
}

/* -------------------------------- work pass -------------------------------- */

export interface CompassCriterion {
  code: string; // C1..C6
  name: string;
  detail: string;
  points: number;
  verdict: Verdict;
}

export interface CompassReport {
  jobId: string;
  jobTitle: string;
  company: string;
  location: string;
  needed: number;
  criteria: CompassCriterion[];
  closingTheGap: string;
  disclaimer: string;
}

/* ----------------------------------- act ----------------------------------- */

export interface BlockedClaim {
  proposed: string;
  reason: string;
  kept: string;
}

export interface ResumeDiff {
  current: string;
  rewritten: string;
  why: string;
}

export interface SkillGap {
  name: string;
  jobs: number;
  pay: string;
  weeks: string;
  where: string;
  note: string;
}

export interface InterviewQuestion {
  question: string;
  use: string;
}

export interface Recruiter {
  name: string;
  role: string;
  why: string;
}

export interface ActionCenter {
  jobId: string;
  jobTitle: string;
  company: string;
  met: number;
  total: number;
  blocked?: BlockedClaim;
  diffs: ResumeDiff[];
  skills: SkillGap[];
  interview: InterviewQuestion[];
  recruiters: Recruiter[];
  draft: string;
}

/* ---------------------------------- watch ---------------------------------- */

export interface WatchEvent {
  time: string;
  title: string;
  body: string;
}

export interface WatchFeed {
  ranAt: string;
  postingsScanned: number;
  scope: string;
  enabled: boolean;
  events: WatchEvent[];
}

/* ---------------------------------- track ---------------------------------- */

export interface TrackerMetric {
  value: string;
  label: string;
}

export interface Application {
  id: string;
  job: string;
  company: string;
  sent: string;
  status: string;
  verdict: Verdict;
}

export interface Tracker {
  metrics: TrackerMetric[];
  applications: Application[];
}

/* ------------------------------- navigation ------------------------------- */

export interface Stage {
  id: string;
  label: string;
  href: string;
}

export interface StageGroup {
  group: string;
  items: Stage[];
}
