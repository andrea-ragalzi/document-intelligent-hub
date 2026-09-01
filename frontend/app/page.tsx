"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileText, FileUp, MessageSquare, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const capabilities = [
  {
    icon: FileUp,
    title: "Upload your PDFs",
    description: "Add the documents you want to explore.",
  },
  {
    icon: MessageSquare,
    title: "Ask questions",
    description: "Ask about their content in normal language.",
  },
  {
    icon: FileText,
    title: "Get answers from your documents",
    description: "Receive answers based on the information contained in your PDFs.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  if (!mounted || loading) {
    return (
      <main className="app-shell flex min-h-screen items-center justify-center" aria-busy="true">
        <p className="text-muted">Loading Document Intelligent Hub…</p>
      </main>
    );
  }

  if (user) {
    return null;
  }

  return (
    <div className="app-shell min-h-screen">
      <nav className="container relative z-10 mx-auto px-4 py-4 sm:px-6 sm:py-5">
        <div className="ui-panel flex items-center justify-between rounded-xl px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-on-accent sm:h-10 sm:w-10">
              <Sparkles className="h-5 w-5" aria-hidden="true" />
            </div>
            <span className="text-base font-semibold tracking-tight text-ink sm:text-xl">
              Document Intelligent Hub
            </span>
          </div>
          <button
            type="button"
            onClick={() => router.push("/login")}
            className="rounded-lg px-4 py-2 text-sm font-medium text-muted transition-colors hover:bg-surface-hover hover:text-ink focus:outline-none focus:ring-3 focus:ring-focus sm:px-5 sm:text-base"
          >
            Login
          </button>
        </div>
      </nav>

      <main>
        <section className="container relative z-10 mx-auto px-4 pb-16 pt-14 text-center sm:px-6 sm:pb-24 sm:pt-20">
          <h1 className="mx-auto max-w-4xl text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-6xl md:text-7xl">
            Ask questions about your PDFs.
            <br />
            Get answers from your documents.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted sm:mt-6 sm:text-xl">
            Upload your PDFs, ask questions in plain language, and get answers based on the
            information they contain.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:mt-10 sm:flex-row sm:gap-4">
            <button
              type="button"
              onClick={() => router.push("/signup")}
              className="ui-primary-action group inline-flex min-h-12 items-center justify-center gap-2 rounded-lg px-6 py-3 text-base font-semibold transition-colors focus:outline-none focus:ring-3 focus:ring-focus sm:px-8 sm:text-lg"
            >
              Try the demo
              <ArrowRight
                className="h-5 w-5 transition-transform group-hover:translate-x-1"
                aria-hidden="true"
              />
            </button>
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="ui-secondary-action inline-flex min-h-12 items-center justify-center rounded-lg px-6 py-3 text-base font-semibold transition-colors focus:outline-none focus:ring-3 focus:ring-focus sm:px-8 sm:text-lg"
            >
              View GitHub
            </a>
          </div>
        </section>

        <section className="container relative z-10 mx-auto px-4 pb-16 sm:px-6 sm:pb-24">
          <div className="grid gap-4 sm:grid-cols-3 sm:gap-6">
            {capabilities.map(({ icon: Icon, title, description }) => (
              <article key={title} className="ui-panel rounded-xl p-6 sm:p-7">
                <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg bg-accent/12 text-accent">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <h2 className="text-xl font-semibold text-ink">{title}</h2>
                <p className="mt-2 leading-relaxed text-muted">{description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="container relative z-10 mx-auto flex flex-col items-center justify-between gap-4 border-t border-line/15 px-4 py-8 text-sm text-muted sm:flex-row sm:px-6 sm:py-10">
        <span>© {new Date().getFullYear()} Document Intelligent Hub</span>
        <div className="flex items-center gap-5">
          <a className="transition-colors hover:text-accent" href="/about">
            About
          </a>
          <a
            className="transition-colors hover:text-accent"
            href="https://github.com/andrea-ragalzi/document-intelligent-hub"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
