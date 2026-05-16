import "./globals.css";
import type { Metadata } from "next";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "PLBets v2 — Premier League Intelligence",
  description:
    "Real-time Premier League prediction dashboard. Fixtures, model-driven probabilities, SHAP explainability, and betting market context.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Nav />
        <main className="max-w-7xl mx-auto px-5 py-8">{children}</main>
        <footer className="max-w-7xl mx-auto px-5 py-10 text-xs text-ink-muted border-t border-line mt-12">
          PLBets v2 · Powered by football-data.org · Built for analysis, not advice.
        </footer>
      </body>
    </html>
  );
}
