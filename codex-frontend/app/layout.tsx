import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "CodexEngine",
  description: "Self-hosted document intelligence — upload PDFs, ask questions, get cited answers from your private knowledge base.",
  keywords: ["document Q&A", "RAG", "self-hosted", "PDF chat", "vector search", "pgvector", "knowledge base"],
  openGraph: {
    title: "CodexEngine",
    description: "Self-hosted document intelligence — upload PDFs, ask questions, get cited answers from your private knowledge base.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CodexEngine",
    description: "Self-hosted document intelligence — upload PDFs, ask questions, get cited answers from your private knowledge base.",
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn("h-full", "antialiased", "dark", inter.variable, jetbrainsMono.variable, "font-sans")}
    >
      <body className="min-h-full flex flex-col">
        <TooltipProvider delay={200}>
          {children}
          <Toaster />
        </TooltipProvider>
      </body>
    </html>
  );
}
