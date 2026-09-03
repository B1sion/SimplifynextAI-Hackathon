import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono } from "next/font/google";
import { Rail } from "@/components/rail";
import { fetchSessionSummary, fetchStages } from "@/lib/api";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "Evidence",
    template: "%s · Evidence",
  },
  description: "Job matching that shows its working.",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const [stages, session] = await Promise.all([fetchStages(), fetchSessionSummary()]);

  return (
    <html lang="en" className={`${archivo.variable} ${plexMono.variable}`}>
      <body>
        <div className="shell">
          <Rail stages={stages} session={session} />
          <main className="canvas">{children}</main>
        </div>
      </body>
    </html>
  );
}
