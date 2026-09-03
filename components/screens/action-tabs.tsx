"use client";

import { useState } from "react";
import { Button, ButtonLink, Card, Nav, SectionHead } from "@/components/ui";
import type { ActionCenter } from "@/lib/types";

type TabId = "tailor" | "learn" | "prep" | "reach";

const TABS: [TabId, string][] = [
  ["tailor", "Tailor my resume"],
  ["learn", "Tell me what to learn"],
  ["prep", "Prepare me for the interview"],
  ["reach", "Help me contact someone"],
];

export function ActionTabs({ center }: { center: ActionCenter }) {
  const [tab, setTab] = useState<TabId>("tailor");

  return (
    <>
      <div className="tabs" role="tablist">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className="tab"
            data-on={tab === id ? "1" : "0"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "tailor" && <TailorTab center={center} />}
      {tab === "learn" && <LearnTab center={center} />}
      {tab === "prep" && <PrepTab center={center} />}
      {tab === "reach" && <ReachTab center={center} />}
    </>
  );
}

/* ------------------------------- tailor ------------------------------- */

function TailorTab({ center }: { center: ActionCenter }) {
  const [approved, setApproved] = useState<boolean[]>(() => center.diffs.map((_, i) => i < 2));
  const count = approved.filter(Boolean).length;

  return (
    <>
      <p className="sub">
        The writer drafted {center.diffs.length + 1} bullets. {center.diffs.length === 3 ? "Three" : center.diffs.length}{" "}
        are below for you to approve. The last one never reached you.
      </p>

      <div className="blockcard">
        <div className="blockhead">
          <i className="pulse stop" />
          Validator blocked one rewrite
        </div>
        <div style={{ padding: "17px 22px" }}>
          <div style={{ fontSize: 11.5, color: "var(--block)", marginBottom: 7 }}>The writer proposed</div>
          <div className="strike" style={{ fontSize: 14, lineHeight: 1.55 }}>
            {center.blocked.proposed}
          </div>
          <div
            style={{
              marginTop: 15,
              paddingTop: 14,
              borderTop: "1px solid rgba(158,43,43,.22)",
              fontSize: 13.5,
              lineHeight: 1.65,
            }}
          >
            {center.blocked.reason}
          </div>
          <div style={{ marginTop: 15, paddingTop: 14, borderTop: "1px solid rgba(158,43,43,.22)" }}>
            <div style={{ fontSize: 11.5, color: "var(--ink3)", marginBottom: 7 }}>Kept instead</div>
            <div style={{ fontSize: 14, lineHeight: 1.55 }}>{center.blocked.kept}</div>
          </div>
        </div>
      </div>

      {center.diffs.map((d, i) => (
        <Card key={i} style={{ marginBottom: 14 }}>
          <div className="diffhead">
            <span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Bullet {i + 1}</span>
            <Button
              sm
              ghost={!approved[i]}
              onClick={() => setApproved((a) => a.map((v, k) => (k === i ? !v : v)))}
            >
              {approved[i] ? "Approved" : "Approve this change"}
            </Button>
          </div>
          <div className="diff">
            <div>
              <div className="difflabel">Currently</div>
              <div style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--ink2)" }}>{d.current}</div>
            </div>
            <div>
              <div className="difflabel">Rewritten</div>
              <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>{d.rewritten}</div>
            </div>
          </div>
          <div style={{ padding: "11px 20px", borderTop: "1px solid var(--rule2)", fontSize: 12.5, color: "var(--ink3)" }}>
            {d.why}
          </div>
        </Card>
      ))}

      <Nav>
        {/* TODO(backend): POST /jobs/:id/resume with the approved diff indexes; returns a file to download. */}
        <ButtonLink href="/track">
          Download resume with {count} change{count === 1 ? "" : "s"}
        </ButtonLink>
      </Nav>
    </>
  );
}

/* -------------------------------- learn -------------------------------- */

function LearnTab({ center }: { center: ActionCenter }) {
  return (
    <>
      <p className="sub">
        Three requirements you are missing, ordered by what each one opens up across the roles we track — not just
        this job.
      </p>
      <Card>
        {center.skills.map((s) => (
          <div className="skill" key={s.name}>
            <div style={{ fontSize: 17, fontWeight: 600, letterSpacing: "-0.015em" }}>{s.name}</div>
            <div style={{ fontSize: 13, color: "var(--ink2)", marginTop: 4, lineHeight: 1.55, maxWidth: "64ch" }}>
              {s.note}
            </div>
            <div className="stats">
              <div className="stat">
                <b>{s.jobs}</b>
                <span>more jobs open up</span>
              </div>
              <div className="stat">
                <b>{s.pay}</b>
                <span>on advertised salary</span>
              </div>
              <div className="stat">
                <b>{s.weeks}</b>
                <span>to a working level</span>
              </div>
            </div>
            <div
              style={{
                marginTop: 14,
                paddingTop: 13,
                borderTop: "1px solid var(--rule2)",
                fontSize: 13,
                color: "var(--ink2)",
                lineHeight: 1.6,
              }}
            >
              {s.where}
            </div>
          </div>
        ))}
      </Card>
    </>
  );
}

/* -------------------------------- prep --------------------------------- */

function PrepTab({ center }: { center: ActionCenter }) {
  return (
    <>
      <p className="sub">
        Likely questions for this role, including the ones that will poke at your gaps. Each is paired with the story
        from your own resume to answer it with.
      </p>
      <Card>
        {center.interview.map((q, i) => (
          <div
            key={q.question}
            style={{ padding: "18px 24px", borderBottom: i < center.interview.length - 1 ? "1px solid var(--rule2)" : "none" }}
          >
            <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.45 }}>{q.question}</div>
            <div
              style={{
                marginTop: 10,
                paddingLeft: 13,
                borderLeft: "3px solid var(--mark)",
                fontSize: 13.5,
                color: "var(--ink2)",
                lineHeight: 1.6,
              }}
            >
              {q.use}
            </div>
          </div>
        ))}
      </Card>
    </>
  );
}

/* -------------------------------- reach -------------------------------- */

function ReachTab({ center }: { center: ActionCenter }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(center.draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable; nothing to do */
    }
  }

  return (
    <>
      <p className="sub">
        {center.recruiters.length} people at {center.company} worth writing to, and a draft built only from confirmed
        facts.
      </p>
      <div className="split">
        <Card>
          <SectionHead>Your draft</SectionHead>
          <div className="pad">
            <div className="mono" style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.75 }}>
              {center.draft}
            </div>
          </div>
          <div style={{ padding: "13px 24px", borderTop: "1px solid var(--rule2)", display: "flex", gap: 9, flexWrap: "wrap" }}>
            <Button sm onClick={copy}>
              {copied ? "Copied" : "Copy draft"}
            </Button>
            {/* TODO(backend): POST /jobs/:id/draft { mode: "shorter" | "rewrite" } */}
            <Button ghost sm disabled>
              Make it shorter
            </Button>
            <Button ghost sm disabled>
              Rewrite
            </Button>
          </div>
          <div style={{ padding: "0 24px 16px", fontSize: 12, color: "var(--ink3)", lineHeight: 1.55 }}>
            We do not send anything. Copy it, read it once more, send it yourself.
          </div>
        </Card>
        <Card>
          <SectionHead>Likely contacts</SectionHead>
          {center.recruiters.map((r, i) => (
            <div
              key={r.name}
              style={{ padding: "15px 22px", borderBottom: i < center.recruiters.length - 1 ? "1px solid var(--rule2)" : "none" }}
            >
              <div style={{ fontSize: 14.5, fontWeight: 600 }}>{r.name}</div>
              <div style={{ fontSize: 12.5, color: "var(--ink2)", marginTop: 2 }}>{r.role}</div>
              <div style={{ fontSize: 12, color: "var(--ink3)", marginTop: 5 }}>{r.why}</div>
            </div>
          ))}
        </Card>
      </div>
    </>
  );
}
