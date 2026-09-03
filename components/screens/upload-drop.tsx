"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadResume } from "@/lib/api";

/**
 * Drop zone / file picker. Calls the placeholder uploadResume() and moves on to
 * the facts screen. Real parsing happens on the backend later.
 */
export function UploadDrop() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file || busy) return;
    setFileName(file.name);
    setBusy(true);
    try {
      await uploadResume(file);
      router.push("/facts");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="drop"
        data-active={dragging ? "1" : "0"}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          void handleFile(e.dataTransfer.files?.[0]);
        }}
        disabled={busy}
      >
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>
          {busy ? "Reading your resume…" : fileName ?? "Drop your resume here"}
        </div>
        <div style={{ fontSize: 12.5, color: "var(--ink2)" }}>PDF or Word · we never send it anywhere else</div>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        hidden
        onChange={(e) => void handleFile(e.target.files?.[0])}
      />
    </>
  );
}
