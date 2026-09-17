import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NIRIKSHAK (निरीक्षक) — Access Knowledge Framework",
  description: "Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
