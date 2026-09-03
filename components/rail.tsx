"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { SessionSummary, StageGroup } from "@/lib/types";

/**
 * Left-hand step rail. Client component only so it can highlight the current
 * route; everything it renders is passed in from the server layout.
 */
export function Rail({ stages, session }: { stages: StageGroup[]; session: SessionSummary }) {
  const pathname = usePathname();
  // Step numbers run continuously across groups (1..9).
  const offsets = stages.reduce<number[]>((acc, g, i) => [...acc, (acc[i - 1] ?? 0) + (i === 0 ? 0 : stages[i - 1].items.length)], []);

  return (
    <aside className="rail">
      <div className="brand">
        <h1>Evidence</h1>
        <p>Job matching that shows its working</p>
      </div>

      <nav className="steps" aria-label="Steps">
        {stages.map((group, gi) => (
          <div key={group.group}>
            <div className="railgroup">{group.group}</div>
            {group.items.map((stage, si) => {
              const n = offsets[gi] + si + 1;
              const active = pathname === stage.href;
              return (
                <Link
                  key={stage.id}
                  href={stage.href}
                  className="step"
                  data-on={active ? "1" : "0"}
                  aria-current={active ? "page" : undefined}
                >
                  <span className="n">{n}</span>
                  <span>{stage.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="railfoot">
        {session.candidateName}
        <br />
        {session.factsConfirmed} facts confirmed · {session.claimsBlocked} claim{session.claimsBlocked === 1 ? "" : "s"} blocked
        <br />
        <span style={{ display: "inline-block", marginTop: 7 }}>
          <span className="livedot" />
          Watch ran {session.lastWatchRun}
        </span>
      </div>
    </aside>
  );
}
