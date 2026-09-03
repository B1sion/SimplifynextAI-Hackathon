import type { Metadata } from "next";
import { FactList } from "@/components/screens/fact-list";
import { ButtonLink, Nav, PageHeader } from "@/components/ui";
import { fetchFacts } from "@/lib/api";

export const metadata: Metadata = { title: "Check the facts" };

export default async function FactsPage() {
  const groups = await fetchFacts();
  const count = groups.reduce((sum, g) => sum + g.items.length, 0);

  return (
    <>
      <PageHeader
        eyebrow="Set up · step 2"
        title={`We read ${count} facts. Check them.`}
        sub="Everything below came from a specific line. If we got something wrong, fix it now — every match, rewrite and interview answer later on is built from this list and nothing else."
      />

      <FactList groups={groups} />

      <Nav>
        <ButtonLink href="/profile">These are correct</ButtonLink>
        <ButtonLink href="/" ghost>
          Upload a different resume
        </ButtonLink>
      </Nav>
    </>
  );
}
