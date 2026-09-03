import { describe, expect, it } from "vitest";
import { getPersonalDocumentCount } from "@/components/RightSidebar/MenuProfileSection";

describe("getPersonalDocumentCount", () => {
  it("does not count the bundled demo document against the visible quota", () => {
    expect(
      getPersonalDocumentCount([
        { filename: "alice-demo.pdf", chunks_count: 3, is_demo_document: true },
        { filename: "private.pdf", chunks_count: 4, is_demo_document: false },
      ])
    ).toBe(1);
  });
});
