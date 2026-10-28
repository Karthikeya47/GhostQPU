import type { Metadata } from "next";
import { Big_Shoulders, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const display = Big_Shoulders({ variable: "--f-display", subsets: ["latin"], weight: ["500", "800", "900"] });
const sans = IBM_Plex_Sans({ variable: "--f-sans", subsets: ["latin"], weight: ["400", "500", "600"] });
const mono = IBM_Plex_Mono({ variable: "--f-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "GhostQPU",
  description: "Hidden canary circuits catch quantum jobs that were simulated from IBM's public calibration data.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable} ${mono.variable}`}>{children}</body>
    </html>
  );
}
