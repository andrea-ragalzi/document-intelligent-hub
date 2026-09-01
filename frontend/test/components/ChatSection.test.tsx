import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatSection } from "@/components/ChatSection";

vi.mock("@/components/ChatSection/useChatScroll", () => ({
  useChatScroll: () => ({ current: null }),
}));

vi.mock("@/components/ChatSection/useLanguageFlag", () => ({
  useLanguageFlag: () => ({
    isLanguageSelectorOpen: false,
    setIsLanguageSelectorOpen: vi.fn(),
    languageFlag: "🇬🇧",
  }),
}));

describe("ChatSection", () => {
  it("renders one chat icon in the new-conversation empty state", () => {
    const { container } = render(
      <ChatSection
        chatHistory={[]}
        query=""
        isQuerying={false}
        userId="user-a"
        onQueryChange={vi.fn()}
        onQuerySubmit={vi.fn()}
        hasDocuments
        isCheckingDocuments={false}
        onOpenUploadModal={vi.fn()}
        selectedOutputLanguage="EN"
        onSelectOutputLanguage={vi.fn()}
        demoDocumentState="idle"
        suggestedQuestions={[]}
        onSuggestedQuestion={vi.fn()}
      />
    );

    expect(container.querySelectorAll("svg.lucide-message-square")).toHaveLength(1);
  });

  it("renders repeated assistant text without duplicate React keys", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <ChatSection
        chatHistory={[
          { type: "user", text: "Question one", sources: [] },
          { type: "assistant", text: "No answer found", sources: [] },
          { type: "user", text: "Question two", sources: [] },
          { type: "assistant", text: "No answer found", sources: [] },
        ]}
        query=""
        isQuerying={false}
        userId="user-a"
        onQueryChange={vi.fn()}
        onQuerySubmit={vi.fn()}
        hasDocuments
        isCheckingDocuments={false}
        onOpenUploadModal={vi.fn()}
        selectedOutputLanguage="EN"
        onSelectOutputLanguage={vi.fn()}
        demoDocumentState="idle"
        suggestedQuestions={[]}
        onSuggestedQuestion={vi.fn()}
      />
    );

    expect(
      consoleError.mock.calls.some(([message]) =>
        String(message).includes("Encountered two children with the same key")
      )
    ).toBe(false);
    consoleError.mockRestore();
  });
});
