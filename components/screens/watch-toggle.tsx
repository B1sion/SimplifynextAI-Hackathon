"use client";

import { useState, useTransition } from "react";
import { setWatchEnabled } from "@/lib/api";

export function WatchToggle({ initial }: { initial: boolean }) {
  const [on, setOn] = useState(initial);
  const [pending, startTransition] = useTransition();

  function toggle() {
    const next = !on;
    setOn(next);
    startTransition(async () => {
      await setWatchEnabled(next);
    });
  }

  return (
    <button type="button" className="toggle" role="switch" aria-checked={on} onClick={toggle} disabled={pending}>
      <span className="switch" data-on={on ? "1" : "0"}>
        <i />
      </span>
      <span style={{ fontSize: 13.5 }}>{on ? "On" : "Off"}</span>
    </button>
  );
}
