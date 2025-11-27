"use client";

import {
  Info,
  Code,
  Shield,
  MessageSquare,
  AlertTriangle,
  ArrowLeft,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AboutPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-purple-900 dark:to-indigo-950">
      {/* Animated background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-300 dark:bg-purple-600 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-300 dark:bg-blue-600 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-indigo-300 dark:bg-indigo-600 rounded-full mix-blend-multiply dark:mix-blend-soft-light filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="sticky top-0 z-20 backdrop-blur-md bg-white/70 dark:bg-gray-900/70 border-b border-purple-200 dark:border-purple-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push("/dashboard")}
                className={
                  "p-2 hover:bg-purple-100 dark:hover:bg-purple-900/50 rounded-lg " +
                  "transition-all duration-200 group focus:outline-none focus:ring-3 " +
                  "focus:ring-focus min-h-[44px] min-w-[44px] flex items-center justify-center"
                }
                aria-label="Back to dashboard"
              >
                <ArrowLeft
                  size={24}
                  className="text-purple-700 dark:text-purple-300 group-hover:-translate-x-1 transition-transform"
                />
              </button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg shadow-lg">
                  <Info size={24} className="text-white" />
                </div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent">
                  About Document Intelligent Hub
                </h1>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
          <div className="space-y-8">
            {/* Introduction */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-purple-100 dark:border-purple-900 hover:scale-[1.02]">
              <p className="text-base text-gray-700 dark:text-gray-200 leading-relaxed">
                This is the{" "}
                <strong className="text-purple-600 dark:text-purple-400">
                  Minimum Viable Product (MVP)
                </strong>{" "}
                for the Document Intelligent Hub—a secure, AI-powered system
                designed to analyze and synthesize information from your
                uploaded files using advanced{" "}
                <strong className="text-indigo-600 dark:text-indigo-400">
                  Retrieval-Augmented Generation (RAG)
                </strong>{" "}
                technology.
              </p>
            </section>

            {/* Technology and Limits */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-purple-100 dark:border-purple-900 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <Code size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent">
                  Technology and Usage Limits
                </h2>
              </div>
              <div className="space-y-6 text-base text-gray-700 dark:text-gray-200">
                <p>
                  <strong>Core Engine:</strong> The system uses a
                  Retrieval-Augmented Generation (RAG) architecture, powered by{" "}
                  <code className="px-3 py-1 bg-gradient-to-r from-purple-100 to-indigo-100 dark:from-purple-900 dark:to-indigo-900 rounded-lg text-sm font-mono border border-purple-200 dark:border-purple-700">
                    GPT-4o Mini
                  </code>
                  , to provide context-aware answers based on your documents.
                </p>
                <div className="p-6 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950 dark:to-indigo-950 border-2 border-purple-200 dark:border-purple-800 rounded-xl shadow-inner">
                  <p className="font-semibold mb-4 text-base text-purple-900 dark:text-purple-100">
                    Current Limits (Public RELEASE):
                  </p>
                  <ul className="space-y-3 ml-4 text-base">
                    <li className="flex items-start gap-3">
                      <span className="text-purple-600 dark:text-purple-400 font-bold">
                        •
                      </span>
                      <span>
                        <strong>Max Documents per User:</strong> 3 files
                      </span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-purple-600 dark:text-purple-400 font-bold">
                        •
                      </span>
                      <span>
                        <strong>Max File Size:</strong> 15 MB per document
                      </span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-purple-600 dark:text-purple-400 font-bold">
                        •
                      </span>
                      <span>
                        <strong>Max Queries per Day:</strong> 50 queries
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            {/* RAG Disclaimer */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-yellow-200 dark:border-yellow-900 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <AlertTriangle size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 dark:from-yellow-400 dark:to-orange-400 bg-clip-text text-transparent">
                  RAG Disclaimer (Read Carefully)
                </h2>
              </div>
              <div className="p-6 bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-950 dark:to-orange-950 border-2 border-yellow-300 dark:border-yellow-800 rounded-xl">
                <p className="text-base text-gray-700 dark:text-gray-200 leading-relaxed">
                  ⚠️ As an MVP using advanced AI, the system may occasionally
                  produce inaccurate or unfounded information (&ldquo;
                  <strong className="text-yellow-700 dark:text-yellow-300">
                    Hallucinations
                  </strong>
                  &rdquo;). Please <strong>verify all critical details</strong>{" "}
                  against the source cited by the system in each response.
                </p>
              </div>
            </section>

            {/* Data Privacy */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <Shield size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 dark:from-green-400 dark:to-emerald-400 bg-clip-text text-transparent">
                  Data Privacy and Security
                </h2>
              </div>
              <div className="space-y-6">
                <p className="text-base text-gray-700 dark:text-gray-200 leading-relaxed">
                  We are committed to the security of your data. The following
                  guarantees are critical to the system&apos;s architecture:
                </p>
                <div className="space-y-4">
                  <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 border-2 border-green-200 dark:border-green-800 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <p className="font-semibold mb-3 text-base text-green-900 dark:text-green-100">
                      🔒 Document Storage:
                    </p>
                    <p className="text-base text-gray-700 dark:text-gray-200">
                      Your documents are{" "}
                      <strong className="text-green-600 dark:text-green-400">
                        NOT saved on the server
                      </strong>
                      . Once processed into secure numerical representations
                      (vectors), the original files are discarded from server
                      memory.
                    </p>
                  </div>
                  <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 border-2 border-green-200 dark:border-green-800 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                    <p className="font-semibold mb-3 text-base text-green-900 dark:text-green-100">
                      🛡️ External Transmission:
                    </p>
                    <p className="text-base text-gray-700 dark:text-gray-200">
                      The content of your documents is{" "}
                      <strong className="text-green-600 dark:text-green-400">
                        NOT sent to OpenAI
                      </strong>
                      . Only small, relevant sections (chunks) retrieved by the
                      RAG system are sent to GPT-4o Mini for synthesis,
                      protecting the overall integrity of your files.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Authorship */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <Code size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent">
                  Authorship and Source Code
                </h2>
              </div>
              <div className="p-6 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950 dark:to-indigo-950 border-2 border-purple-200 dark:border-purple-800 rounded-xl space-y-4 text-base">
                <p className="text-gray-700 dark:text-gray-200">
                  This project was built from the ground up to demonstrate
                  proficiency in secure, scalable AI architecture.
                </p>
                <div className="space-y-3 text-base text-gray-700 dark:text-gray-200">
                  <p>
                    <strong className="text-purple-600 dark:text-purple-400">
                      Developed By:
                    </strong>{" "}
                    Andrea Ragalzi
                  </p>
                  <p>
                    <strong className="text-purple-600 dark:text-purple-400">
                      Source Code (GitHub):
                    </strong>{" "}
                    <a
                      href="https://github.com/andrea-ragalzi/document-intelligent-hub"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 dark:text-purple-400 hover:text-indigo-600 dark:hover:text-indigo-400 underline decoration-2 underline-offset-2 font-medium transition-colors"
                    >
                      github.com/andrea-ragalzi/document-intelligent-hub
                    </a>
                  </p>
                  <p>
                    <strong className="text-purple-600 dark:text-purple-400">
                      Portfolio:
                    </strong>{" "}
                    <a
                      href="https://andrearagalzi.netlify.app/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 dark:text-purple-400 hover:text-indigo-600 dark:hover:text-indigo-400 underline decoration-2 underline-offset-2 font-medium transition-colors"
                    >
                      andrearagalzi.netlify.app
                    </a>
                  </p>
                </div>
              </div>
            </section>

            {/* Feedback and Support */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <MessageSquare size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 dark:from-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
                  Feedback and Support
                </h2>
              </div>
              <div className="p-6 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 border-2 border-blue-200 dark:border-blue-800 rounded-xl">
                <p className="text-base text-gray-700 dark:text-gray-200 mb-6 leading-relaxed">
                  Please help us refine the system by reporting any issues you
                  encounter or sharing your thoughts on the experience.
                </p>
                <div className="space-y-4 text-base text-gray-700 dark:text-gray-200">
                  <div className="flex items-start gap-3">
                    <span className="text-blue-600 dark:text-blue-400 text-xl">
                      📋
                    </span>
                    <div>
                      <strong className="text-blue-600 dark:text-blue-400">
                        Report a Bug:
                      </strong>{" "}
                      Use the &ldquo;Report Bug&rdquo; button in the dashboard
                      menu to submit detailed bug reports with optional
                      attachments.
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-blue-600 dark:text-blue-400 text-xl">
                      ⭐
                    </span>
                    <div>
                      <strong className="text-blue-600 dark:text-blue-400">
                        Give Feedback:
                      </strong>{" "}
                      Use the &ldquo;Give Feedback&rdquo; button to rate your
                      experience and share comments.
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* How the System Works */}
            <section className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                  <Info size={24} className="text-white" />
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent">
                  How the System Works
                </h2>
              </div>
              <div className="space-y-4 text-base text-gray-700 dark:text-gray-200">
                <p>
                  The RAG is an expert, professional assistant that follows
                  strict operational rules:
                </p>
                <ul className="space-y-3 ml-2">
                  <li className="flex items-start gap-3">
                    <span className="text-purple-600 dark:text-purple-400 font-bold text-base mt-1">
                      •
                    </span>
                    <div>
                      <strong className="text-purple-600 dark:text-purple-400">
                        Source Citation:
                      </strong>{" "}
                      Every response includes a reference to the source
                      document(s) used.
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-purple-600 dark:text-purple-400 font-bold text-base mt-1">
                      •
                    </span>
                    <div>
                      <strong className="text-purple-600 dark:text-purple-400">
                        Contextual Memory:
                      </strong>{" "}
                      The system maintains conversation history to answer
                      follow-up questions accurately.
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-purple-600 dark:text-purple-400 font-bold text-base mt-1">
                      •
                    </span>
                    <div>
                      <strong className="text-purple-600 dark:text-purple-400">
                        Handling Gaps:
                      </strong>{" "}
                      If information is not found in your documents, the system
                      will clearly state this rather than fabricating answers.
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-purple-600 dark:text-purple-400 font-bold text-base mt-1">
                      •
                    </span>
                    <div>
                      <strong className="text-purple-600 dark:text-purple-400">
                        Language:
                      </strong>{" "}
                      The system responds in the same language as your query
                      (supports 20+ languages).
                    </div>
                  </li>
                </ul>
              </div>
            </section>

            {/* Back to Dashboard Button */}
            <div className="flex justify-center pt-4">
              <button
                onClick={() => router.push("/dashboard")}
                className={
                  "group relative px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 " +
                  "hover:from-purple-700 hover:to-indigo-700 active:from-purple-800 active:to-indigo-800 " +
                  "text-white rounded-lg transition-all duration-300 font-semibold text-base " +
                  "focus:outline-none focus:ring-3 focus:ring-focus shadow-lg hover:shadow-xl " +
                  "hover:scale-105 overflow-hidden min-h-[44px]"
                }
                aria-label="Return to dashboard"
              >
                <span className="relative z-10 flex items-center gap-3">
                  <span>Back to Dashboard</span>
                  <span className="transform group-hover:translate-x-1 transition-transform">
                    →
                  </span>
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
