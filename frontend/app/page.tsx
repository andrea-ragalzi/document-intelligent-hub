"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, MessageSquare, Zap, Shield, ArrowRight, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function LandingPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  if (!mounted || loading) {
    return (
      <main className="app-shell min-h-screen flex items-center justify-center" aria-busy="true">
        <p className="text-muted">Loading Document Intelligent Hub…</p>
      </main>
    );
  }

  // Don't show landing page if user is authenticated
  if (user) {
    return null;
  }

  const features = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: "Document Upload",
      description:
        "Upload PDF documents and extract knowledge instantly with AI-powered processing.",
    },
    {
      icon: <MessageSquare className="w-6 h-6" />,
      title: "Intelligent Chat",
      description:
        "Ask questions in natural language and get accurate answers from your documents.",
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Fast & Efficient",
      description: "Powered by ChromaDB vector storage and OpenAI for lightning-fast responses.",
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Secure & Private",
      description:
        "Your documents are stored securely with Firebase authentication and multi-tenant isolation.",
    },
  ];

  const technologies = [
    "FastAPI",
    "Next.js 16",
    "React 19",
    "LangChain",
    "ChromaDB",
    "OpenAI GPT-4",
    "Firebase",
    "Firestore",
    "TypeScript",
    "Python",
    "Docker",
    "Zustand",
    "TanStack Query",
    "Tailwind CSS",
    "HuggingFace",
    "Pydantic",
  ];

  return (
    <div className="app-shell min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-accent/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-line/5 rounded-full blur-3xl"></div>
        </div>

        {/* Navigation */}
        <nav className="relative z-10 container mx-auto px-4 sm:px-6 py-4 sm:py-5">
          <div className="ui-panel rounded-xl px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
            <div className="flex items-center gap-2 sm:gap-2.5">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-accent rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-on-accent" />
              </div>
              <span className="text-base sm:text-xl font-semibold tracking-tight text-ink">
                Document Intelligent Hub
              </span>
            </div>
            <div className="flex gap-2 sm:gap-3">
              <button
                onClick={() => router.push("/login")}
                className="px-4 sm:px-5 py-2 sm:py-2.5 text-sm sm:text-base text-muted hover:text-ink font-medium transition-colors rounded-lg hover:bg-surface-hover"
              >
                Login
              </button>
              <button
                onClick={() => router.push("/signup")}
                className="ui-primary-action px-4 sm:px-6 py-2 sm:py-2.5 text-sm sm:text-base rounded-lg transition-colors font-semibold"
              >
                Get Started
              </button>
            </div>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-4 sm:px-6 pt-12 sm:pt-20 pb-20 sm:pb-32 text-center">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-accent/10 border border-accent/20 rounded-full text-accent text-xs sm:text-sm font-medium mb-6 sm:mb-8">
            <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />
            AI-Powered Document Intelligence
          </div>

          <h1 className="text-3xl sm:text-5xl md:text-7xl font-semibold tracking-tight mb-4 sm:mb-6 text-ink leading-tight px-4">
            Transform Your Documents
            <br />
            Into Conversations
          </h1>

          <p className="text-base sm:text-xl md:text-2xl text-muted mb-8 sm:mb-12 max-w-3xl mx-auto px-4">
            Upload your PDFs, ask questions in natural language, and get intelligent answers powered
            by advanced RAG technology.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4">
            <button
              onClick={() => router.push("/signup")}
              className="ui-primary-action group px-6 sm:px-8 py-3 sm:py-4 rounded-lg transition-colors text-base sm:text-lg font-semibold flex items-center justify-center gap-2"
            >
              Start Free Now
              <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="ui-secondary-action px-6 sm:px-8 py-3 sm:py-4 rounded-lg transition-colors text-base sm:text-lg font-semibold flex items-center justify-center gap-2"
            >
              <svg
                className="w-4 h-4 sm:w-5 sm:h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
              View on GitHub
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20">
        <div className="text-center mb-10 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight mb-3 sm:mb-4 text-ink">
            Everything You Need
          </h2>
          <p className="text-lg sm:text-xl text-muted">
            Powerful features to make your documents work for you
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {features.map(feature => (
            <div
              key={feature.title}
              className="ui-panel p-8 rounded-xl transition-colors group hover:border-line/30"
            >
              <div className="w-12 h-12 bg-accent/12 rounded-lg flex items-center justify-center text-accent mb-3 sm:mb-4 group-hover:bg-accent/18 transition-colors">
                {feature.icon}
              </div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-ink">
                {feature.title}
              </h3>
              <p className="text-sm sm:text-base text-muted">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How It Works Section */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 py-16 sm:py-24">
        <div className="ui-subtle-panel rounded-2xl p-8 sm:p-12 lg:p-16">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight mb-3 sm:mb-4 text-ink">
              How It Works
            </h2>
            <p className="text-lg sm:text-xl text-muted">Get started in three simple steps</p>
          </div>

          <div className="grid sm:grid-cols-3 gap-10 sm:gap-12 max-w-5xl mx-auto">
            {[
              {
                step: "1",
                title: "Upload",
                desc: "Upload your PDF documents to the secure platform",
              },
              {
                step: "2",
                title: "Process",
                desc: "AI automatically extracts and indexes the content",
              },
              {
                step: "3",
                title: "Chat",
                desc: "Ask questions and get instant, accurate answers",
              },
            ].map(item => (
              <div key={item.step} className="text-center">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-accent rounded-full flex items-center justify-center text-on-accent text-2xl sm:text-3xl font-semibold mx-auto mb-5 sm:mb-6">
                  {item.step}
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4 text-ink">
                  {item.title}
                </h3>
                <p className="text-sm sm:text-base text-muted leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Technologies Section */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20">
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight mb-3 sm:mb-4 text-ink">
            Built With Modern Technologies
          </h2>
          <p className="text-lg sm:text-xl text-muted">
            Powered by industry-leading tools and frameworks
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
          {technologies.map(tech => (
            <div
              key={tech}
              className="px-4 sm:px-6 py-2 sm:py-3 bg-surface rounded-full border border-line/15 text-muted text-sm sm:text-base font-medium hover:bg-surface-hover hover:text-ink transition-colors"
            >
              {tech}
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20">
        <div className="bg-raised border border-line/15 rounded-2xl p-8 sm:p-12 md:p-20 text-center text-ink">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-base sm:text-xl mb-6 sm:mb-8 opacity-90">
            Join now and start chatting with your documents in seconds.
          </p>
          <button
            onClick={() => router.push("/signup")}
            className="ui-primary-action px-6 sm:px-8 py-3 sm:py-4 rounded-lg transition-colors text-base sm:text-lg font-semibold inline-flex items-center gap-2"
          >
            Create Free Account
            <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 container mx-auto px-4 sm:px-6 py-8 sm:py-12 border-t border-line/15">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 sm:gap-4">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
            <span className="text-lg sm:text-xl font-semibold text-ink">
              Document Intelligent Hub
            </span>
          </div>
          <div className="flex gap-4 sm:gap-6 text-sm sm:text-base text-muted">
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-accent transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub/wiki"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-accent transition-colors"
            >
              Documentation
            </a>
          </div>
          <a
            href="https://andrearagalzi.netlify.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-quiet text-sm"
          >
            © {new Date().getFullYear()} Andrea Ragalzi
          </a>
        </div>
      </footer>
    </div>
  );
}
