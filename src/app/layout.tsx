import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { DisclaimerModal } from "@/components/course/DisclaimerModal";
import { AudienceOnboardingModal } from "@/components/course/AudienceOnboardingModal";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://learngenai.sunmintz.com"),
  title: "Learn GenAI",
  description: "A structured, practical curriculum from foundational LLMs to fully autonomous Agentic systems.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>
        {children}
        <DisclaimerModal />
        <AudienceOnboardingModal />
      </body>
    </html>
  );
}
