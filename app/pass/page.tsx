import type { Metadata } from "next";
import { ButtonLink, Card, Nav, PageHeader, SectionHead, VERDICT_COLORS } from "@/components/ui";
import { fetchCompassReport } from "@/lib/api";
import { jobQuery } from "@/lib/routes";

export const metadata: Metadata = { title: "Work pass check" };

export default async function PassPage({ searchParams }: PageProps<"/pass">) {
  const { job } = await searchParams;
  const jobId = typeof job === "string" ? job : undefined;
  const report = await fetchCompassReport(jobId);
  const total = report.criteria.reduce((sum, c) => sum + c.points, 0);
  const passes = total >= report.needed;

  return (
    <>
      <PageHeader
        eyebrow={`${report.jobTitle} · ${report.company} · ${report.location}`}
        title="Can you actually take this job?"
        sub="A skills match is worthless if the employer cannot get you a pass. We score every role against the six COMPASS criteria before you apply, so the ones that will never clear are labelled rather than ranked."
      />

      <Card>
        <SectionHead aside="estimate">COMPASS criteria</SectionHead>
        {report.criteria.map((c) => {
          const [bg, fg] = VERDICT_COLORS[c.verdict];
          return (
            <div className="crit" key={c.code}>
              <div>
                <div className="critname">{c.name}</div>
                <div className="critdesc">{c.detail}</div>
              </div>
              <div className="pts" style={{ background: bg, color: fg }}>
                {c.points} pts
              </div>
              <div style={{ fontSize: 12, color: "var(--ink3)" }}>{c.code}</div>
            </div>
          );
        })}
        <div className="total">
          <b style={{ color: passes ? "var(--verify)" : "var(--block)" }}>{total}</b>
          <span style={{ fontSize: 14, color: "var(--ink2)" }}>
            of the {report.needed} points an application needs to pass
          </span>
        </div>
      </Card>

      <Card style={{ marginTop: 18 }}>
        <SectionHead>What would close the gap</SectionHead>
        <div className="pad" style={{ fontSize: 13.5, lineHeight: 1.7, color: "var(--ink2)" }}>
          {report.closingTheGap}
          <div
            style={{
              marginTop: 16,
              paddingTop: 14,
              borderTop: "1px solid var(--rule2)",
              fontSize: 12.5,
              color: "var(--ink3)",
            }}
          >
            {report.disclaimer}
          </div>
        </div>
      </Card>

      <Nav>
        <ButtonLink href={`/act${jobQuery(jobId)}`}>Take action on the gaps</ButtonLink>
        <ButtonLink href={`/match${jobQuery(jobId)}`} ghost>
          Back to the match report
        </ButtonLink>
      </Nav>
    </>
  );
}
