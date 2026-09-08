import { describe, expect, it } from "vitest";
import { toAiSdkMessages } from "@/lib/chatMessagePersistence";

describe("toAiSdkMessages", () => {
  it("rehydrates structured citations as assistant annotations", () => {
    expect(
      toAiSdkMessages("conversation-1", [
        { type: "user", text: "What does it say?", sources: [] },
        {
          type: "assistant",
          text: "The answer is in the document.",
          sources: [{ filename: "document.pdf", page_number: 7 }],
        },
      ])
    ).toEqual([
      {
        id: "loaded-conversation-1-0",
        role: "user",
        content: "What does it say?",
      },
      {
        id: "loaded-conversation-1-1",
        role: "assistant",
        content: "The answer is in the document.",
        annotations: [{ type: "sources", sources: [{ filename: "document.pdf", page_number: 7 }] }],
      },
    ]);
  });

  it("preserves multiple citations and filename-only legacy sources", () => {
    const [assistantMessage] = toAiSdkMessages("conversation-2", [
      {
        type: "assistant",
        text: "Grounded answer",
        sources: [
          { filename: "first.pdf", page_number: 3 },
          { filename: "second.pdf", page_number: 8 },
          "legacy.pdf",
        ],
      },
    ]);

    expect(assistantMessage.annotations).toEqual([
      {
        type: "sources",
        sources: [
          { filename: "first.pdf", page_number: 3 },
          { filename: "second.pdf", page_number: 8 },
          "legacy.pdf",
        ],
      },
    ]);
  });

  it("loads legacy messages without sources normally", () => {
    expect(
      toAiSdkMessages("conversation-3", [{ type: "assistant", text: "Older answer" }])
    ).toEqual([
      {
        id: "loaded-conversation-3-0",
        role: "assistant",
        content: "Older answer",
      },
    ]);
  });
});
