"use client";

import { useState } from "react";
import { Button, Card, Highlight, SectionHead } from "@/components/ui";
import type { FactGroup } from "@/lib/types";

/**
 * Grouped list of parsed facts with Edit / Remove controls.
 * Remove is local-only for now; Edit is a placeholder.
 * TODO(backend): persist edits/removals (PATCH /resumes/:id/facts/:factId).
 */
export function FactList({ groups: initial }: { groups: FactGroup[] }) {
  const [groups, setGroups] = useState(initial);

  function remove(groupName: string, value: string) {
    setGroups((gs) =>
      gs
        .map((g) => (g.group === groupName ? { ...g, items: g.items.filter((f) => f.value !== value) } : g))
        .filter((g) => g.items.length > 0),
    );
  }

  return (
    <Card>
      {groups.map((g) => (
        <div key={g.group}>
          <SectionHead>{g.group}</SectionHead>
          {g.items.map((f) => (
            <div className="factrow" key={f.value}>
              <div>
                <div className="factname">{f.value}</div>
                <div className="factmeta">{f.location}</div>
              </div>
              <div style={{ color: "var(--ink2)" }}>
                <Highlight>{f.source}</Highlight>
              </div>
              <div style={{ display: "flex", gap: 7 }}>
                <Button ghost sm onClick={() => window.alert("Editing facts is not wired up yet.")}>
                  Edit
                </Button>
                <Button ghost sm onClick={() => remove(g.group, f.value)}>
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </Card>
  );
}
