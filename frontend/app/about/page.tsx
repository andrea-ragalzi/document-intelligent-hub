"use client";

import { AlertTriangle, ArrowLeft, Code, Info, MessageSquare, Shield } from "lucide-react";
import { useRouter } from "next/navigation";

const sectionClassName = "ui-panel rounded-xl p-6 sm:p-8";
const headingClassName = "text-xl font-semibold text-ink";
const iconClassName = "rounded-lg bg-accent p-2.5 text-on-accent";

export default function AboutPage() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-20 border-b border-line/15 bg-canvas/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-muted transition-colors hover:bg-surface-hover hover:text-ink focus:outline-none focus:ring-3 focus:ring-focus"
            aria-label="Back to dashboard"
          >
            <ArrowLeft size={22} />
          </button>
          <div className="flex items-center gap-3">
            <span className={iconClassName}>
              <Info size={22} />
            </span>
            <h1 className="text-xl font-semibold text-ink sm:text-2xl">
              About Document Intelligent Hub
            </h1>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
        <section className={sectionClassName}>
          <p className="leading-relaxed text-muted">
            This is the <strong className="text-accent">Minimum Viable Product (MVP)</strong> for
            the Document Intelligent Hub—a secure, AI-powered system designed to analyze and
            synthesize information from your uploaded files using advanced{" "}
            <strong className="text-accent">Retrieval-Augmented Generation (RAG)</strong>{" "}
            technology.
          </p>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className={iconClassName}>
              <Code size={22} />
            </span>
            <h2 className={headingClassName}>Technology and Usage Limits</h2>
          </div>
          <div className="space-y-5 leading-relaxed text-muted">
            <p>
              <strong className="text-ink">Core Engine:</strong> The system uses a
              Retrieval-Augmented Generation architecture and a configured OpenAI model to provide
              context-aware answers based on your documents.
            </p>
            <div className="ui-subtle-panel rounded-lg p-5">
              <p className="mb-3 font-semibold text-ink">Current limits for public FREE access</p>
              <ul className="space-y-2">
                <li>
                  <span className="mr-2 text-accent">•</span>
                  <strong>Max documents per user:</strong> 5 files
                </li>
                <li>
                  <span className="mr-2 text-accent">•</span>
                  <strong>Max file size:</strong> 10 MB per PDF
                </li>
                <li>
                  <span className="mr-2 text-accent">•</span>
                  <strong>Max queries per day:</strong> 20 queries
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className="rounded-lg bg-warning p-2.5 text-canvas">
              <AlertTriangle size={22} />
            </span>
            <h2 className={headingClassName}>RAG Disclaimer</h2>
          </div>
          <div className="rounded-lg border border-warning/35 bg-warning/10 p-5 leading-relaxed text-muted">
            The system may occasionally produce inaccurate or unfounded information. Please{" "}
            <strong className="text-ink">verify critical details</strong> against the source cited
            in each response.
          </div>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className={iconClassName}>
              <Shield size={22} />
            </span>
            <h2 className={headingClassName}>Data Privacy and Security</h2>
          </div>
          <div className="space-y-4 text-muted">
            <p className="leading-relaxed">
              Your data is protected through per-user isolation in Firebase and ChromaDB.
            </p>
            <div className="ui-subtle-panel rounded-lg p-5">
              <p className="mb-2 font-semibold text-ink">Document storage</p>
              <p className="leading-relaxed">
                Original files are processed for indexing and discarded from temporary server
                memory; only document vectors and metadata required by the RAG system persist.
              </p>
            </div>
            <div className="ui-subtle-panel rounded-lg p-5">
              <p className="mb-2 font-semibold text-ink">External transmission</p>
              <p className="leading-relaxed">
                Only relevant retrieved document sections are sent to the configured OpenAI model to
                generate an answer.
              </p>
            </div>
          </div>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className={iconClassName}>
              <Code size={22} />
            </span>
            <h2 className={headingClassName}>Authorship and Source Code</h2>
          </div>
          <div className="space-y-3 leading-relaxed text-muted">
            <p>This project demonstrates a secure, scalable Python and RAG architecture.</p>
            <p>
              <strong className="text-ink">Developed by:</strong> Andrea Ragalzi
            </p>
            <p>
              <strong className="text-ink">Source code:</strong>{" "}
              <a
                className="text-accent underline underline-offset-2 hover:text-accent-hover"
                href="https://github.com/andrea-ragalzi/document-intelligent-hub"
                target="_blank"
                rel="noopener noreferrer"
              >
                github.com/andrea-ragalzi/document-intelligent-hub
              </a>
            </p>
            <p>
              <strong className="text-ink">Portfolio:</strong>{" "}
              <a
                className="text-accent underline underline-offset-2 hover:text-accent-hover"
                href="https://andrearagalzi.netlify.app/"
                target="_blank"
                rel="noopener noreferrer"
              >
                andrearagalzi.netlify.app
              </a>
            </p>
          </div>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className={iconClassName}>
              <MessageSquare size={22} />
            </span>
            <h2 className={headingClassName}>Feedback and Support</h2>
          </div>
          <div className="space-y-3 leading-relaxed text-muted">
            <p>Please help refine the system by reporting issues or sharing feedback.</p>
            <p>
              <strong className="text-ink">Report a bug:</strong> use the Report Bug option in the
              dashboard menu.
            </p>
            <p>
              <strong className="text-ink">Give feedback:</strong> use the Give Feedback option in
              the dashboard menu.
            </p>
          </div>
        </section>

        <section className={sectionClassName}>
          <div className="mb-6 flex items-center gap-3">
            <span className={iconClassName}>
              <Info size={22} />
            </span>
            <h2 className={headingClassName}>How the System Works</h2>
          </div>
          <ul className="space-y-3 leading-relaxed text-muted">
            <li>
              <span className="mr-2 text-accent">•</span>
              <strong className="text-ink">Source citation:</strong> every response includes its
              source documents.
            </li>
            <li>
              <span className="mr-2 text-accent">•</span>
              <strong className="text-ink">Contextual memory:</strong> conversation history supports
              follow-up questions.
            </li>
            <li>
              <span className="mr-2 text-accent">•</span>
              <strong className="text-ink">Handling gaps:</strong> the assistant states when
              information is not in the documents.
            </li>
            <li>
              <span className="mr-2 text-accent">•</span>
              <strong className="text-ink">Language:</strong> the system responds in the language of
              your query.
            </li>
          </ul>
        </section>

        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="ui-primary-action min-h-11 rounded-lg px-6 py-3 font-semibold transition-colors focus:outline-none focus:ring-3 focus:ring-focus"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </main>
  );
}
