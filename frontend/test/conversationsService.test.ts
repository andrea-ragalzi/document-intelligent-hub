import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ChatMessage } from "@/lib/types";

const firestore = vi.hoisted(() => ({
  addDoc: vi.fn(),
  collection: vi.fn(() => ({ id: "conversations" })),
  getDocs: vi.fn(),
  query: vi.fn(),
  serverTimestamp: vi.fn(() => "server-timestamp"),
  where: vi.fn(),
}));

vi.mock("firebase/firestore", () => ({
  ...firestore,
  deleteDoc: vi.fn(),
  doc: vi.fn(),
  updateDoc: vi.fn(),
}));

vi.mock("@/lib/firebase", () => ({
  getFirebaseAuth: () => ({ currentUser: { uid: "user-a" } }),
  getFirebaseDb: () => ({ id: "database" }),
}));

import {
  loadConversationsFromFirestore,
  saveConversationToFirestore,
} from "@/lib/conversationsService";

const structuredHistory: ChatMessage[] = [
  { type: "user", text: "Where is the answer?", sources: [] },
  {
    type: "assistant",
    text: "It is on page seven.",
    sources: [
      { filename: "document.pdf", page_number: 7 },
      { filename: "appendix.pdf", page_number: 2 },
    ],
  },
];

describe("conversation citation persistence", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    firestore.addDoc.mockResolvedValue({ id: "conversation-1" });
  });

  it("persists structured citations with the assistant message", async () => {
    await saveConversationToFirestore("user-a", "Citation test", structuredHistory);

    expect(firestore.addDoc).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ history: structuredHistory })
    );
  });

  it("keeps page numbers and multiple citations through a Firestore load", async () => {
    firestore.getDocs.mockResolvedValue({
      forEach: (callback: (snapshot: { id: string; data: () => unknown }) => void) =>
        callback({
          id: "conversation-1",
          data: () => ({
            userId: "user-a",
            name: "Citation test",
            history: structuredHistory,
            createdAt: { toDate: () => new Date("2026-01-01T00:00:00.000Z") },
          }),
        }),
    });

    const [conversation] = await loadConversationsFromFirestore("user-a");

    expect(conversation.history).toEqual(structuredHistory);
  });
});
