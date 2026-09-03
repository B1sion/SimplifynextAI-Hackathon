import type { Metadata } from "next";
import { JobList } from "@/components/screens/job-list";
import { PageHeader } from "@/components/ui";
import { fetchDiscoverSummary, fetchJobs, fetchUnlocks } from "@/lib/api";

export const metadata: Metadata = { title: "Find jobs" };

export default async function DiscoverPage() {
  const [unlocks, summary, closeJobs, browseJobs] = await Promise.all([
    fetchUnlocks(),
    fetchDiscoverSummary(),
    fetchJobs("close"),
    fetchJobs("browse"),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Match · step 4"
        title="How do you want to look?"
        sub="Either way, every job carries a tag telling you whether the door is actually open."
      />

      <div className="unlockwrap">
        <div className="unlockhead">
          <h3>One skill changes the shape of your whole search</h3>
          <p>
            Measured across all {summary.totalRoles.toLocaleString()} open roles, not just the one you are looking at.
            This is what each missing requirement is costing you right now.
          </p>
        </div>
        {unlocks.map((u) => (
          <div className="unlockrow" key={u.name}>
            <b>{u.name}</b>
            <span className="unlockbar">
              <i style={{ width: `${u.pct}%` }} />
            </span>
            <span style={{ color: "var(--ink2)" }}>{u.jobs} roles open up</span>
            <span style={{ color: "var(--ink2)" }}>{u.weeks}</span>
          </div>
        ))}
      </div>

      <JobList summary={summary} closeJobs={closeJobs} browseJobs={browseJobs} />
    </>
  );
}
