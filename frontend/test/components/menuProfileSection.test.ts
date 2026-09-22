import { describe, expect, it } from "vitest";
import { getPersonalDocumentCount } from "@/components/RightSidebar/MenuProfileSection";

describe("getPersonalDocumentCount", () => {
  it("counts the bundled demo document like every other document", () => {
    expect(
      getPersonalDocumentCount([
        { filename: "alice-demo.pdf", chunks_count: 3, is_demo_document: true },
        { filename: "private.pdf", chunks_count: 4 },
      ])
    ).toBe(2);
  });
});
