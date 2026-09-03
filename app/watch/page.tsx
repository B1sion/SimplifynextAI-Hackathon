import type { Metadata } from "next";
import { WatchToggle } from "@/components/screens/watch-toggle";
import { ButtonLink, Card, Nav, PageHeader, SectionHead } from "@/components/ui";
import { fetchWatchFeed } from "@/lib/api";

export const metadata: Metadata = { title: "Overnight watch" };

export default async function WatchPage() {
  const feed = await fetchWatchFeed();

  return (
    <>
      <PageHeader
        eyebrow={`Ran at ${feed.ranAt} · ${feed.postingsScanned.toLocaleString()} postings rescanned`}
        title="What changed while you slept."
        sub="The search does not stop when you close the tab. Overnight the ranker rescans every posting against your confirmed facts, and reports only what actually moved."
      />

      <Card style={{ marginBottom: 18 }}>
        <div
          className="pad"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 18, flexWrap: "wrap" }}
        >
          <div>
            <div style={{ fontSize: 14.5, fontWeight: 600 }}>Watching: {feed.scope}</div>
            <div style={{ fontSize: 12.5, color: "var(--ink2)", marginTop: 3 }}>
              Rescans nightly · alerts only when something changes your standing
            </div>
          </div>
          <WatchToggle initial={feed.enabled} />
        </div>
      </Card>

      <Card>
        <SectionHead aside={`${feed.events.length} changes`}>Last night</SectionHead>
        {feed.events.map((e) => (
          <div className="watchitem" key={e.time + e.title}>
            <div className="watchtime">{e.time}</div>
            <div>
              <div className="watchtitle">{e.title}</div>
              <div className="watchbody">{e.body}</div>
            </div>
          </div>
        ))}
      </Card>

      <Nav>
        <ButtonLink href="/discover">See the updated list</ButtonLink>
        <ButtonLink href="/track" ghost>
          Go to tracker
        </ButtonLink>
      </Nav>
    </>
  );
}
