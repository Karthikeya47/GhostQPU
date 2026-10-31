import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Bundled (Latin subset, OFL) so builds never depend on reaching Google Fonts, which failed in CI and offline.
const display = localFont({ src: "./fonts/Unbounded-latin.woff2", weight: "300 700", variable: "--f-display", display: "swap" });
const sans = localFont({ src: "./fonts/IBMPlexSans-latin.woff2", weight: "400 600", variable: "--f-sans", display: "swap" });
const mono = localFont({
  src: [{ path: "./fonts/IBMPlexMono-400-latin.woff2", weight: "400" }, { path: "./fonts/IBMPlexMono-500-latin.woff2", weight: "500" }],
  variable: "--f-mono",
  display: "swap",
});

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
