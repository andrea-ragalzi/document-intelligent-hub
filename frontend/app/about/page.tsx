"use client";

import { ArrowLeft, Info } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function AboutPage() {
  const router = useRouter();
  const { user } = useAuth();
  const returnPath = user ? "/dashboard" : "/";
  const returnLabel = user ? "Back to dashboard" : "Back to home";

  return (
    <main className="app-shell min-h-screen text-ink">
      <header className="border-b border-line/15 bg-canvas/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-4 sm:px-6 sm:py-5">
          <button
            type="button"
            onClick={() => router.push(returnPath)}
            className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-muted transition-colors hover:bg-surface-hover hover:text-ink focus:outline-none focus:ring-3 focus:ring-focus"
            aria-label={returnLabel}
          >
            <ArrowLeft size={22} />
          </button>
          <div className="flex items-center gap-3">
            <span className="rounded-lg bg-accent p-2.5 text-on-accent">
              <Info size={22} aria-hidden="true" />
            </span>
            <h1 className="text-xl font-semibold text-ink sm:text-2xl">
              About Document Intelligent Hub
            </h1>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-16">
        <div className="max-w-3xl space-y-5 text-base leading-relaxed text-muted sm:text-lg">
          <p>
            Document Intelligent Hub is an independent full-stack RAG application built around a
            Python and FastAPI backend.
          </p>
          <p>
            It processes uploaded documents, retrieves relevant information from ChromaDB, and uses
            an LLM to generate answers grounded in the user&apos;s documents.
          </p>
        </div>

        <section
          className="ui-subtle-panel mt-10 rounded-xl p-6 sm:mt-12 sm:p-8"
          aria-labelledby="technical-overview"
        >
          <h2 id="technical-overview" className="text-lg font-semibold text-ink sm:text-xl">
            Technical overview
          </h2>
          <dl className="mt-5 grid gap-x-8 gap-y-4 sm:grid-cols-2">
            <div>
              <dt className="font-semibold text-ink">Backend</dt>
              <dd className="mt-1 text-muted">Python · FastAPI · Pydantic</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">RAG</dt>
              <dd className="mt-1 text-muted">ChromaDB · LangChain · OpenAI</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Authentication</dt>
              <dd className="mt-1 text-muted">Firebase</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink">Frontend</dt>
              <dd className="mt-1 text-muted">Next.js</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="font-semibold text-ink">Engineering</dt>
              <dd className="mt-1 text-muted">
                REST APIs · testing · integrations · user data isolation
              </dd>
            </div>
          </dl>
        </section>

        <div className="mt-10 max-w-3xl border-t border-line/15 pt-8 text-base leading-relaxed text-muted sm:mt-12 sm:text-lg">
          <p>
            The backend separates application logic from infrastructure such as vector storage,
            authentication and external AI services. Automated tests cover the critical application
            and RAG workflows.
          </p>
        </div>

        <p className="mt-8 text-sm text-muted">
          Built by{" "}
          <a
            href="https://andrea-ragalzi.github.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-accent underline underline-offset-2 transition-colors hover:text-accent-hover focus:outline-none focus:ring-3 focus:ring-focus"
          >
            Andrea Ragalzi
          </a>
        </p>

        <button
          type="button"
          onClick={() => router.push(returnPath)}
          className="ui-primary-action mt-8 inline-flex min-h-11 items-center rounded-lg px-5 py-3 font-semibold transition-colors focus:outline-none focus:ring-3 focus:ring-focus"
        >
          {returnLabel}
        </button>
      </section>
    </main>
  );
}
