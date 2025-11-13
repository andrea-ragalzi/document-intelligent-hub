"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  MessageSquare,
  Zap,
  Shield,
  ArrowRight,
  Github,
  Sparkles,
} from "lucide-react";
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
    return null;
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
      description:
        "Powered by ChromaDB vector storage and OpenAI for lightning-fast responses.",
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
    "Next.js",
    "LangChain",
    "ChromaDB",
    "OpenAI",
    "Firebase",
    "TypeScript",
    "Docker",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-300 dark:bg-purple-900 rounded-full opacity-20 blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-300 dark:bg-blue-900 rounded-full opacity-20 blur-3xl"></div>
        </div>

        {/* Navigation */}
        <nav className="relative z-10 container mx-auto px-6 py-6 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
              Document Hub
            </span>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => router.push("/login")}
              className="px-6 py-2 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => router.push("/signup")}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Get Started
            </button>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-6 pt-20 pb-32 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-700 dark:text-blue-300 text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" />
            AI-Powered Document Intelligence
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 dark:from-white dark:via-blue-200 dark:to-purple-200 bg-clip-text text-transparent leading-tight">
            Transform Your Documents
            <br />
            Into Conversations
          </h1>

          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-12 max-w-3xl mx-auto">
            Upload your PDFs, ask questions in natural language, and get
            intelligent answers powered by advanced RAG technology.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push("/signup")}
              className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-xl hover:shadow-2xl transform hover:-translate-y-1 text-lg font-semibold flex items-center justify-center gap-2"
            >
              Start Free Now
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1 text-lg font-semibold flex items-center justify-center gap-2 border border-gray-200 dark:border-gray-700"
            >
              <Github className="w-5 h-5" />
              View on GitHub
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">
            Everything You Need
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Powerful features to make your documents work for you
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all border border-gray-100 dark:border-gray-700 group hover:-translate-y-1"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* How It Works Section */}
      <div className="relative z-10 container mx-auto px-6 py-20 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-800 rounded-3xl my-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">
            How It Works
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Get started in three simple steps
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
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
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                {item.step}
              </div>
              <h3 className="text-2xl font-semibold mb-3 text-gray-900 dark:text-white">
                {item.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Technologies Section */}
      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">
            Built With Modern Technologies
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Powered by industry-leading tools and frameworks
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-4">
          {technologies.map((tech, index) => (
            <div
              key={index}
              className="px-6 py-3 bg-white dark:bg-gray-800 rounded-full shadow-md border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all"
            >
              {tech}
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 md:p-20 text-center text-white shadow-2xl">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join now and start chatting with your documents in seconds.
          </p>
          <button
            onClick={() => router.push("/signup")}
            className="px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-all shadow-xl hover:shadow-2xl transform hover:-translate-y-1 text-lg font-semibold inline-flex items-center gap-2"
          >
            Create Free Account
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 container mx-auto px-6 py-12 border-t border-gray-200 dark:border-gray-800">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              Document Hub
            </span>
          </div>
          <div className="flex gap-6 text-gray-600 dark:text-gray-400">
            <a
              href="https://github.com/andrea-ragalzi/document-intelligent-hub"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              GitHub
            </a>
            <a
              href="#"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              Documentation
            </a>
            <a
              href="#"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              About
            </a>
          </div>
          <p className="text-gray-500 dark:text-gray-500 text-sm">
            © 2025 Document Hub. Open Source.
          </p>
        </div>
      </footer>
    </div>
  );
}
