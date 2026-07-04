import type { Metadata } from "next";
import { Geist, Geist_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

// Body: Geist — clean, neutral, highly readable.
const sans = Geist({
  variable: "--ff-sans",
  subsets: ["latin"],
});

// Utility / data / code: Geist Mono — powers tags, timestamps, and the
// tabular-numeral points & streak values that are our signature detail.
const mono = Geist_Mono({
  variable: "--ff-mono",
  subsets: ["latin"],
});

// Display / headings: Space Grotesk — geometric, engineered feel; reads
// "technical" without shouting. Used with restraint on headings only.
const display = Space_Grotesk({
  variable: "--ff-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Vultr Developer Community",
  description: "A developer community forum with a challenge & rewards engine.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // `dark` forces our dark-only palette; the font variables expose the faces.
      className={`dark ${sans.variable} ${mono.variable} ${display.variable} h-full`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
