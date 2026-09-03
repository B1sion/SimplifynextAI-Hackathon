"use client";

import { useState } from "react";
import { ButtonLink, Card, Highlight, SectionHead } from "@/components/ui";
import type { MatchReport } from "@/lib/types";

/** Requirement list with a sticky evidence panel; selecting a row shows its proof. */
export function MatchReportView({ report, passHref }: { report: MatchReport; passHref: string }) {
  const firstMet = Math.max(0, report.requirements.findIndex((r) => r.met));
  const [active, setActive] = useState(firstMet);
  const current = report.requirements[active];

  return (
    <div className="split">
      <Card>
        <SectionHead aside="select to see proof">Requirements, checked one by one</SectionHead>
        {report.requirements.map((r, i) => (
          <button
            type="button"
            className="req"
            key={r.text}
            data-on={active === i ? "1" : "0"}
            onClick={() => setActive(i)}
          >
            <span className="reqicon" style={{ background: r.met ? "var(--verify)" : "var(--caution)" }}>
              {r.met ? "✓" : "!"}
            </span>
            <span>
              <span className="reqtext">{r.text}</span>
              {!r.met && <span className="reqnote">{r.note}</span>}
            </span>
          </button>
        ))}
      </Card>

      <div className="stickyside">
        <Card style={{ marginBottom: 14 }}>
          <SectionHead>{current.met ? "The line that proves it" : "Nothing in your resume covers this"}</SectionHead>
          <div className="pad">
            {current.met ? (
              <>
                <Highlight>{current.evidence}</Highlight>
                <div style={{ fontSize: 12, color: "var(--ink3)", marginTop: 10 }}>{current.location}</div>
              </>
            ) : (
              <div style={{ fontSize: 13.5, color: "var(--ink2)", lineHeight: 1.6 }}>{current.note}</div>
            )}
          </div>
        </Card>

        <Card>
          <SectionHead>Work pass</SectionHead>
          <div className="pad">
            <div className="bigscore" style={{ marginBottom: 10 }}>
              <b style={{ color: report.workPass.points >= report.workPass.needed ? "var(--verify)" : "var(--block)" }}>
                {report.workPass.points}
              </b>
              <span>of {report.workPass.needed} points needed</span>
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--ink2)" }}>{report.workPass.summary}</div>
            <ButtonLink href={passHref} ghost sm style={{ marginTop: 14 }}>
              See the full breakdown
            </ButtonLink>
          </div>
        </Card>
      </div>
    </div>
  );
}
