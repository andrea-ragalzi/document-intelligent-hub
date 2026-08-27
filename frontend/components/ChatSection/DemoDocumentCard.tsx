import { FileText, Loader, Paperclip } from "lucide-react";
import type { DemoDocumentState } from "@/hooks/useDemoDocument";

interface DemoDocumentCardProps {
  state: DemoDocumentState;
  suggestedQuestions: string[];
  onSelectQuestion: (question: string) => void;
  onOpenUpload: () => void;
}

export function DemoDocumentCard({
  state,
  suggestedQuestions,
  onSelectQuestion,
  onOpenUpload,
}: DemoDocumentCardProps) {
  if (state === "idle") return null;

  if (state === "seeding") {
    return (
      <div className="mx-auto mt-6 max-w-xl rounded-xl border border-indigo-200 bg-white/70 p-4 text-left dark:border-indigo-800 dark:bg-indigo-900/30">
        <p className="flex items-center gap-2 font-semibold text-indigo-800 dark:text-indigo-100">
          <Loader size={18} className="animate-spin" /> Preparing your private demo document…
        </p>
        <button
          type="button"
          onClick={onOpenUpload}
          className="mt-2 text-sm text-indigo-700 underline dark:text-indigo-200"
        >
          You can also upload your own PDF.
        </button>
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div className="mx-auto mt-6 max-w-xl rounded-xl border border-amber-200 bg-amber-50 p-4 text-left dark:border-amber-800 dark:bg-amber-900/20">
        <p className="font-semibold text-amber-900 dark:text-amber-100">
          Demo document unavailable
        </p>
        <button
          type="button"
          onClick={onOpenUpload}
          className="mt-2 text-sm text-amber-800 underline dark:text-amber-200"
        >
          You can still upload your own PDF.
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto mt-6 max-w-xl rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-left dark:border-emerald-800 dark:bg-emerald-900/20">
      <p className="flex items-center gap-2 font-semibold text-emerald-900 dark:text-emerald-100">
        <FileText size={18} /> Demo document ready
      </p>
      <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
        Try one of these questions:
      </p>
      <div className="mt-3 flex flex-col items-start gap-2">
        {suggestedQuestions.map(question => (
          <button
            key={question}
            type="button"
            onClick={() => onSelectQuestion(question)}
            className="text-left text-sm text-indigo-700 underline decoration-indigo-300 underline-offset-2 dark:text-indigo-200"
          >
            {question}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={onOpenUpload}
        className="mt-4 flex items-center gap-1 text-sm text-emerald-800 underline dark:text-emerald-200"
      >
        <Paperclip size={14} /> You can also upload your own PDF.
      </button>
    </div>
  );
}
