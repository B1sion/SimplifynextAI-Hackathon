import type { Metadata } from "next";
import { ButtonLink, Card, Nav, PageHeader, Tag } from "@/components/ui";
import { fetchTracker } from "@/lib/api";

export const metadata: Metadata = { title: "Track progress" };

export default async function TrackPage() {
  const tracker = await fetchTracker();
  const sent = tracker.applications.length;

  return (
    <>
      <PageHeader
        eyebrow="Ongoing"
        title="Everything you have sent."
        sub={`${sent} application${sent === 1 ? "" : "s"}, all tailored from the same confirmed facts.`}
      />

      <div className="metrics">
        {tracker.metrics.map((m) => (
          <div className="metric" key={m.label}>
            <b>{m.value}</b>
            <span>{m.label}</span>
          </div>
        ))}
      </div>

      <Card>
        <div className="trow thead">
          <span>Role</span>
          <span>Company</span>
          <span>Sent</span>
          <span>Status</span>
          <span />
        </div>
        {tracker.applications.map((a) => (
          <div className="trow" key={a.id}>
            <span style={{ fontWeight: 600 }}>{a.job}</span>
            <span style={{ color: "var(--ink2)" }}>{a.company}</span>
            <span style={{ color: "var(--ink2)" }}>{a.sent}</span>
            <span>
              <Tag verdict={a.verdict}>{a.status}</Tag>
            </span>
            <span>
              {/* TODO(backend): link to /applications/:id once that view exists. */}
              <ButtonLink href="/match" ghost sm>
                Open
              </ButtonLink>
            </span>
          </div>
        ))}
      </Card>

      <Nav>
        <ButtonLink href="/discover">Look for more jobs</ButtonLink>
        <ButtonLink href="/watch" ghost>
          See last night&apos;s changes
        </ButtonLink>
      </Nav>
    </>
  );
}
