import type { Metadata } from "next";
import { ProfileForm } from "@/components/screens/profile-form";
import { PageHeader } from "@/components/ui";
import { fetchProfileQuestions } from "@/lib/api";

export const metadata: Metadata = { title: "Three questions" };

export default async function ProfilePage() {
  const questions = await fetchProfileQuestions();

  return (
    <>
      <PageHeader
        eyebrow="Set up · step 3"
        title="Three things a resume never says."
        sub="These decide whether a role is actually open to you, not just a good skills fit. A job you cannot legally take should not be sitting at the top of your list."
      />
      <ProfileForm questions={questions} />
    </>
  );
}
