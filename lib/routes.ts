/**
 * Route helpers. The per-job screens (/match, /pass, /act) take an optional
 * `?job=<id>` search param; without it the API layer falls back to a default job.
 */
export function jobQuery(jobId?: string): string {
  return jobId ? `?job=${encodeURIComponent(jobId)}` : "";
}
