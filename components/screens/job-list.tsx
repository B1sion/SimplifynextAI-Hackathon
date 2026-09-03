"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, Tag } from "@/components/ui";
import type { DiscoverSummary, Job } from "@/lib/types";

type Mode = "close" | "browse";

export function JobList({
  summary,
  closeJobs,
  browseJobs,
}: {
  summary: DiscoverSummary;
  closeJobs: Job[];
  browseJobs: Job[];
}) {
  const [mode, setMode] = useState<Mode>("close");
  const list = mode === "close" ? closeJobs : browseJobs;

  return (
    <>
      <div className="modes">
        <button type="button" className="mode" data-on={mode === "browse" ? "1" : "0"} onClick={() => setMode("browse")}>
          <strong>I know what I want</strong>
          <span>Browse the full list and search by title, company or salary.</span>
        </button>
        <button type="button" className="mode" data-on={mode === "close" ? "1" : "0"} onClick={() => setMode("close")}>
          <strong>Show me what I&apos;m close to</strong>
          <span>We scan all {summary.totalRoles.toLocaleString()} open roles and rank the ones you nearly qualify for.</span>
        </button>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 10,
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 13.5, color: "var(--ink2)" }}>
          {mode === "close"
            ? "Ranked by how few requirements you are missing"
            : `${summary.totalRoles.toLocaleString()} roles · sorted A–Z`}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Tag verdict="v">{summary.canApply} can apply</Tag>
          <Tag verdict="c">{summary.mightNotQualify} might not qualify</Tag>
          <Tag verdict="b">{summary.cannotApply} cannot apply</Tag>
        </div>
      </div>

      <Card>
        {list.map((job, i) => (
          <Link className="job" key={job.id} href={`/match?job=${encodeURIComponent(job.id)}`}>
            <span className="rank">{mode === "close" ? String(i + 1).padStart(2, "0") : ""}</span>
            <span>
              <span className="jtitle">{job.title}</span>
              <span className="jmeta">
                {job.company} · {job.location}
              </span>
            </span>
            <span className="score">
              {job.score} of 10 met
              <span className="bar">
                <i style={{ width: `${job.score * 10}%` }} />
              </span>
            </span>
            <Tag verdict={job.verdict}>{job.verdictLabel}</Tag>
          </Link>
        ))}
      </Card>
    </>
  );
}
