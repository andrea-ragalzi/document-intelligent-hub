import { describe, expect, it, vi } from "vitest";
import type { FormEvent } from "react";
import {
  createSubmitHandler,
  shouldShowChatLoadingSkeleton,
} from "@/components/ChatSection/chatHelpers";

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

describe("query length validation", () => {
  it("does not submit queries over the backend limit", () => {
    const submit = vi.fn();
    const tooLong = "x".repeat(1001);
    const event = { preventDefault: vi.fn() } as unknown as FormEvent;

    const onTooLong = vi.fn();
    createSubmitHandler(tooLong, false, "user-a", false, submit, vi.fn(), onTooLong)(event);

    expect(submit).not.toHaveBeenCalled();
    expect(onTooLong).toHaveBeenCalledOnce();
  });
});
