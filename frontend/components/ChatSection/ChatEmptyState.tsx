/**
 * Empty state component for ChatSection
 */

import { AlertTriangle, MessageSquare, Paperclip } from "lucide-react";
import type { DemoDocumentState } from "@/hooks/useDemoDocument";
import { DemoDocumentCard } from "./DemoDocumentCard";

interface EmptyStateProps {
  isCheckingDocuments: boolean;
  isServerOnline: boolean;
  isLimitReached: boolean;
  noDocuments: boolean;
  demoDocumentState: DemoDocumentState;
  suggestedQuestions: string[];
  onSelectQuestion: (question: string) => void;
  onOpenUpload: () => void;
  isGuestDemo?: boolean;
}

export function ChatEmptyState({
  isCheckingDocuments,
  isServerOnline,
  isLimitReached,
  noDocuments,
  demoDocumentState,
  suggestedQuestions,
  onSelectQuestion,
  onOpenUpload,
  isGuestDemo = false,
}: EmptyStateProps) {
  if (isCheckingDocuments) {
    return (
      <div
        role="status"
        aria-label="Loading document workspace"
        className="mx-auto max-w-xl animate-pulse py-4"
      >
        <div className="mx-auto h-12 w-12 rounded-full bg-raised" />
        <div className="mx-auto mt-5 h-5 w-48 rounded bg-raised" />
        <div className="mx-auto mt-3 h-4 w-72 max-w-full rounded bg-raised" />
        <div className="mt-6 min-h-28 rounded-xl border border-line/15 bg-surface" />
      </div>
    );
  }

  if (isServerOnline === false) {
    return (
      <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-xl border border-red-200 dark:border-red-700">
        <p className="font-bold text-lg text-red-700 dark:text-red-400 flex items-center justify-center">
          <AlertTriangle size={20} className="mr-2" />
          Server Offline
        </p>
        <p className="text-sm text-red-600 dark:text-red-300 mt-2 text-center">
          The backend is currently unavailable. Please check your connection or try again later.
        </p>
      </div>
    );
  }

  if (isLimitReached) {
    return (
      <div className="bg-orange-100 dark:bg-orange-900/30 p-4 rounded-xl border border-orange-200 dark:border-orange-700">
        <p className="font-bold text-lg text-orange-700 dark:text-orange-400 flex items-center justify-center">
          <AlertTriangle size={20} className="mr-2" />
          Query Limit Reached
        </p>
        <p className="text-sm text-orange-600 dark:text-orange-300 mt-2 text-center">
          You&apos;ve reached your daily query limit. Please try again tomorrow.
        </p>
      </div>
    );
  }

  if (demoDocumentState === "seeding") {
    return (
      <DemoDocumentCard
        state={demoDocumentState}
        suggestedQuestions={suggestedQuestions}
        onSelectQuestion={onSelectQuestion}
        onOpenUpload={onOpenUpload}
        isGuestDemo={isGuestDemo}
      />
    );
  }

  if (noDocuments) {
    return (
      <>
        <MessageSquare size={48} className="mx-auto text-quiet" />
        <p className="font-semibold text-lg text-muted">No documents uploaded yet</p>
        <p className="text-sm text-quiet max-w-md mx-auto">
          <Paperclip size={14} className="inline mr-1" />
          Upload a PDF document to start asking questions
        </p>
        <DemoDocumentCard
          state={demoDocumentState}
          suggestedQuestions={suggestedQuestions}
          onSelectQuestion={onSelectQuestion}
          onOpenUpload={onOpenUpload}
          isGuestDemo={isGuestDemo}
        />
      </>
    );
  }

  return (
    <>
      <div className={isGuestDemo ? "hidden sm:block" : undefined}>
        <MessageSquare size={48} className="mx-auto text-quiet" />
        <p className="font-semibold text-lg text-muted">Start a conversation</p>
        <p className="text-sm text-quiet">Ask me anything about your documents!</p>
      </div>
      <DemoDocumentCard
        state={demoDocumentState}
        suggestedQuestions={suggestedQuestions}
        onSelectQuestion={onSelectQuestion}
        onOpenUpload={onOpenUpload}
        isGuestDemo={isGuestDemo}
      />
    </>
  );
}
