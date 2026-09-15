import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ChatMessage } from "@/lib/types";

const firestore = vi.hoisted(() => ({
  addDoc: vi.fn(),
  collection: vi.fn(() => ({ id: "conversations" })),
  deleteDoc: vi.fn(),
  doc: vi.fn(),
  getDocs: vi.fn(),
  query: vi.fn(),
  serverTimestamp: vi.fn(() => "server-timestamp"),
  updateDoc: vi.fn(),
  where: vi.fn(),
}));

const firebase = vi.hoisted(() => ({
  getFirebaseAuth: vi.fn(),
  getFirebaseDb: vi.fn(() => ({ id: "database" })),
}));

vi.mock("firebase/firestore", () => ({
  ...firestore,
}));

vi.mock("@/lib/firebase", () => ({
  getFirebaseAuth: firebase.getFirebaseAuth,
  getFirebaseDb: firebase.getFirebaseDb,
}));

import {
  MAX_PERSISTED_CONVERSATION_TEXT_CHARS,
  MAX_PERSISTED_MESSAGES_PER_CONVERSATION,
  MAX_SAVED_CONVERSATIONS_PER_USER,
  migrateLocalStorageToFirestore,
  loadConversationsFromFirestore,
  saveConversationToFirestore,
  updateConversationHistoryInFirestore,
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
    firebase.getFirebaseAuth.mockReturnValue({
      currentUser: {
        uid: "user-a",
        getIdTokenResult: vi.fn().mockResolvedValue({ claims: { tier: "FREE" } }),
      },
    });
    firestore.addDoc.mockResolvedValue({ id: "conversation-1" });
    firestore.getDocs.mockResolvedValue({ size: 0 });
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

  it("rejects a new conversation once the per-user limit is reached", async () => {
    firestore.getDocs.mockResolvedValue({ size: MAX_SAVED_CONVERSATIONS_PER_USER });

    await expect(
      saveConversationToFirestore("user-a", "One too many", structuredHistory)
    ).rejects.toThrow("Failed to save conversation");

    expect(firestore.addDoc).not.toHaveBeenCalled();
  });

  it("does not apply the conversation-count limit to unlimited users", async () => {
    firestore.getDocs.mockResolvedValue({ size: MAX_SAVED_CONVERSATIONS_PER_USER });
    firebase.getFirebaseAuth.mockReturnValue({
      currentUser: {
        uid: "user-a",
        getIdTokenResult: vi.fn().mockResolvedValue({ claims: { tier: "UNLIMITED" } }),
      },
    } as never);

    firestore.addDoc.mockResolvedValue({ id: "unlimited-conversation" });
    const saved = await saveConversationToFirestore("user-a", "Unlimited", structuredHistory);

    expect(saved.id).toBe("unlimited-conversation");
    expect(firestore.getDocs).not.toHaveBeenCalled();
    expect(firestore.addDoc).toHaveBeenCalledTimes(1);
  });

  it("persists only the most recent bounded message and text history", async () => {
    firestore.getDocs.mockResolvedValue({ size: 0 });
    const history = Array.from(
      { length: MAX_PERSISTED_MESSAGES_PER_CONVERSATION + 2 },
      (_, index) => ({
        type: "user" as const,
        text: `message-${index}-${"x".repeat(400)}`,
        sources: [],
      })
    );

    await saveConversationToFirestore("user-a", "Bounded", history);

    const persistedHistory = firestore.addDoc.mock.calls[0][1].history as ChatMessage[];
    expect(persistedHistory).toHaveLength(MAX_PERSISTED_MESSAGES_PER_CONVERSATION);
    expect(persistedHistory[persistedHistory.length - 1]?.text).toContain("message-41-");
    expect(
      persistedHistory.reduce((total, message) => total + message.text.length, 0)
    ).toBeLessThanOrEqual(MAX_PERSISTED_CONVERSATION_TEXT_CHARS);
  });

  it("bounds history updates before they reach Firestore", async () => {
    const history: ChatMessage[] = [
      {
        type: "assistant",
        text: "x".repeat(MAX_PERSISTED_CONVERSATION_TEXT_CHARS + 1),
        sources: [],
      },
    ];

    await updateConversationHistoryInFirestore("conversation-1", history);

    const persistedHistory = firestore.updateDoc.mock.calls[0][1].history as ChatMessage[];
    expect(persistedHistory).toHaveLength(1);
    expect(persistedHistory[0].text).toHaveLength(MAX_PERSISTED_CONVERSATION_TEXT_CHARS);
  });

  it("migrates only the conversations that fit and bounds each migrated history", async () => {
    firestore.getDocs.mockImplementation(() =>
      Promise.resolve({ size: firestore.addDoc.mock.calls.length })
    );
    const localConversations = Array.from(
      { length: MAX_SAVED_CONVERSATIONS_PER_USER + 2 },
      (_, index) => ({
        id: `local-${index}`,
        name: `Conversation ${index}`,
        timestamp: "2026-01-01 12:00",
        history: [
          {
            type: "user" as const,
            text: "x".repeat(MAX_PERSISTED_CONVERSATION_TEXT_CHARS + 1),
            sources: [],
          },
        ],
      })
    );

    await migrateLocalStorageToFirestore("user-a", localConversations);

    expect(firestore.addDoc).toHaveBeenCalledTimes(MAX_SAVED_CONVERSATIONS_PER_USER);
    for (const [, data] of firestore.addDoc.mock.calls) {
      expect(data.history[0].text).toHaveLength(MAX_PERSISTED_CONVERSATION_TEXT_CHARS);
    }
  });

  it("migrates all local conversations for unlimited users", async () => {
    firebase.getFirebaseAuth.mockReturnValue({
      currentUser: {
        uid: "user-a",
        getIdTokenResult: vi.fn().mockResolvedValue({ claims: { tier: "UNLIMITED" } }),
      },
    } as never);
    firestore.addDoc.mockResolvedValue({ id: "migrated-conversation" });
    const localConversations = Array.from(
      { length: MAX_SAVED_CONVERSATIONS_PER_USER + 3 },
      (_, index) => ({
        id: `local-${index}`,
        name: `Conversation ${index}`,
        timestamp: "2026-01-01 12:00",
        history: structuredHistory,
      })
    );

    await migrateLocalStorageToFirestore("user-a", localConversations);

    expect(firestore.getDocs).not.toHaveBeenCalled();
    expect(firestore.addDoc).toHaveBeenCalledTimes(localConversations.length);
  });
});
