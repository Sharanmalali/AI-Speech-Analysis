import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";

import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AblePro Solutions — AI Mental Health Audio Analytics",
    template: "%s · AblePro Solutions",
  },
  description:
    "AI-powered multi-speaker mental health audio analytics: diarization, Kannada→English transcription, gender/age and typical/atypical speech classification.",
  keywords: [
    "speech analysis",
    "speaker diarization",
    "mental health",
    "Kannada transcription",
    "atypical speech",
  ],
  authors: [{ name: "AblePro Solutions" }],
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a12" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${manrope.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
