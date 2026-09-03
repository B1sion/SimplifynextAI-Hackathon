import type { Metadata } from "next";
import { MatchReportView } from "@/components/screens/match-report";
import { ButtonLink, Card, Nav, PageHeader, Tag } from "@/components/ui";
import { fetchMatchReport } from "@/lib/api";
import { jobQuery } from "@/lib/routes";

export const metadata: Metadata = { title: "Match report" };

export default async function MatchPage({ searchParams }: PageProps<"/match">) {
  const { job } = await searchParams;
  const jobId = typeof job === "string" ? job : undefined;
  const report = await fetchMatchReport(jobId);
  const met = report.requirements.filter((r) => r.met).length;
  const total = report.requirements.length;

  return (
    <>
      <PageHeader eyebrow={`${report.jobTitle} · ${report.company} · ${report.location}`} title="Where you stand on this one." />

      <Card style={{ marginBottom: 18 }}>
        <div
          className="pad"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20, flexWrap: "wrap" }}
        >
          <div className="bigscore">
            <b>
              {met} of {total}
            </b>
            <span>requirements met</span>
          </div>
          <Tag verdict={report.verdict} large>
            {report.verdictLabel}
          </Tag>
        </div>
      </Card>

      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12.5, color: "var(--ink2)", marginBottom: 9, fontWeight: 600 }}>
          {report.agents.length} agents produced this report. Here is what each one did.
        </div>
        <div className="agents">
          {report.agents.map((agent) => (
            <div className="agent" key={agent.name}>
              <div className="an">
                <i className={agent.ok ? "pulse" : "pulse stop"} />
                {agent.name}
              </div>
              <div className="ad">{agent.detail}</div>
            </div>
          ))}
        </div>
      </div>

      <MatchReportView report={report} passHref={`/pass${jobQuery(jobId)}`} />

      <Nav>
        <ButtonLink href={`/act${jobQuery(jobId)}`}>Do something about the gaps</ButtonLink>
        <ButtonLink href="/discover" ghost>
          Back to the list
        </ButtonLink>
      </Nav>
    </>
  );
}
