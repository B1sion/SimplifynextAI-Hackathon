"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Nav } from "@/components/ui";
import { saveProfile } from "@/lib/api";
import type { ProfileQuestion } from "@/lib/types";

export function ProfileForm({ questions }: { questions: ProfileQuestion[] }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [picks, setPicks] = useState<Record<string, number>>(() =>
    Object.fromEntries(questions.map((q) => [q.id, q.defaultPick])),
  );

  const needsPass = questions.some((q) => q.id === "work-status" && q.options[picks[q.id]]?.includes("Employment Pass"));

  function submit() {
    startTransition(async () => {
      await saveProfile(picks);
      router.push("/discover");
    });
  }

  return (
    <>
      <Card style={{ maxWidth: 720 }}>
        {questions.map((q) => (
          <div className="qblock" key={q.id}>
            <div style={{ fontSize: 14.5, fontWeight: 600 }}>{q.question}</div>
            <div className="seg" role="radiogroup" aria-label={q.question}>
              {q.options.map((opt, j) => (
                <button
                  key={opt}
                  type="button"
                  role="radio"
                  aria-checked={picks[q.id] === j}
                  className="segbtn"
                  data-on={picks[q.id] === j ? "1" : "0"}
                  onClick={() => setPicks((p) => ({ ...p, [q.id]: j }))}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        ))}
      </Card>

      {needsPass && (
        <div className="callout caution" style={{ maxWidth: 720 }}>
          Because you need an Employment Pass, we will score every role against the COMPASS framework and tell you
          which ones an employer realistically cannot sponsor — before you spend an evening writing the application.
        </div>
      )}

      <Nav>
        <Button onClick={submit} disabled={pending}>
          {pending ? "Saving…" : "Find jobs"}
        </Button>
      </Nav>
    </>
  );
}
