import { describe, expect, it } from "vitest";
import { shouldShowChatLoadingSkeleton } from "@/components/ChatSection/chatHelpers";

describe("shouldShowChatLoadingSkeleton", () => {
  it("shows a placeholder before the assistant starts replying", () => {
    expect(
      shouldShowChatLoadingSkeleton([{ type: "user", text: "Question", sources: [] }], true)
    ).toBe(true);
  });

  it("hides the placeholder once the streaming assistant message exists", () => {
    expect(
      shouldShowChatLoadingSkeleton(
        [
          { type: "user", text: "Question", sources: [] },
          { type: "assistant", text: "Partial answer", sources: [] },
        ],
        true
      )
    ).toBe(false);
  });
});
