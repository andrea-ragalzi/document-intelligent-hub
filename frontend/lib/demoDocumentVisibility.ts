import type { DemoDocumentState } from "@/hooks/useDemoDocument";

export const DEMO_DOCUMENT_FILENAME = "alices-adventures-in-wonderland.pdf";

interface DocumentSummary {
  filename: string;
  is_demo_document?: boolean;
}

/** Keep Alice-only UI tied to the current backend-backed document list. */
export function getDemoDocumentVisibility(
  documents: DocumentSummary[],
  state: DemoDocumentState,
  suggestedQuestions: string[]
): { state: DemoDocumentState; suggestedQuestions: string[] } {
  const exists = documents.some(document => document.is_demo_document === true);
  return {
    state: state === "seeding" || exists ? state : "idle",
    suggestedQuestions: exists ? suggestedQuestions : [],
  };
}
