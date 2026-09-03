import type { Metadata } from "next";
import { UploadDrop } from "@/components/screens/upload-drop";

export const metadata: Metadata = { title: "Upload resume" };

export default function UploadPage() {
  return (
    <div className="hero">
      <div>
        <h2>It will not write anything your resume cannot prove.</h2>
        <p className="sub" style={{ marginBottom: 26 }}>
          Upload once. Every skill we read is stored next to the line it came from — so when a job says you are 7 out
          of 10, you can see which 7, what proves them, and what a rewrite is allowed to claim on your behalf.
        </p>
        <div className="proofline">
          <div className="mono">Built ETL pipelines in Python (pandas, Airflow) processing 2M+ rows daily</div>
          <div style={{ fontSize: 12, color: "var(--ink3)", marginTop: 5 }}>
            → reads as{" "}
            <span className="mark" style={{ fontWeight: 600 }}>
              Python · pandas · Airflow · pipeline ownership
            </span>
          </div>
        </div>
        <div
          style={{
            marginTop: 22,
            paddingTop: 18,
            borderTop: "1px solid var(--rule)",
            fontSize: 13,
            color: "var(--ink2)",
            lineHeight: 1.65,
            maxWidth: "60ch",
          }}
        >
          Recruiters are already filtering out generated applications. Ours are traceable to a source line, which is
          the only thing that survives being asked about in an interview.
        </div>
      </div>

      <div className="card">
        <div className="pad">
          <UploadDrop />
          <div style={{ fontSize: 12, color: "var(--ink3)", marginTop: 14, lineHeight: 1.55 }}>
            Reading takes about 20 seconds. You will get to correct anything we misread before we match you against a
            single job.
          </div>
        </div>
      </div>
    </div>
  );
}
