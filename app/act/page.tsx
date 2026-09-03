import type { Metadata } from "next";
import { ActionTabs } from "@/components/screens/action-tabs";
import { PageHeader } from "@/components/ui";
import { fetchActionCenter } from "@/lib/api";

export const metadata: Metadata = { title: "Take action" };

export default async function ActPage({ searchParams }: PageProps<"/act">) {
  const { job } = await searchParams;
  const jobId = typeof job === "string" ? job : undefined;
  const center = await fetchActionCenter(jobId);

  return (
    <>
      <PageHeader
        eyebrow={`${center.jobTitle} · ${center.company} · ${center.met} of ${center.total} met`}
        title="What do you want to do?"
      />
      <ActionTabs center={center} />
    </>
  );
}
