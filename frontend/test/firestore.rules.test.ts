import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
  type RulesTestEnvironment,
} from "@firebase/rules-unit-testing";
import {
  Timestamp,
  collection,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  query,
  serverTimestamp,
  setDoc,
  updateDoc,
  where,
} from "firebase/firestore";
import { afterAll, afterEach, beforeAll, describe, it } from "vitest";

const projectId = "demo-dih-firestore";
const rules = readFileSync(resolve(__dirname, "../firestore.rules"), "utf8");
let testEnv: RulesTestEnvironment;

const conversation = (owner = "alice", overrides: Record<string, unknown> = {}) => ({
  userId: owner,
  name: "Alice conversation",
  history: [{ type: "user", text: "Hello", sources: [] }],
  createdAt: Timestamp.fromDate(new Date("2026-01-01T00:00:00.000Z")),
  updatedAt: Timestamp.fromDate(new Date("2026-01-01T00:00:00.000Z")),
  isPinned: false,
  ...overrides,
});

const database = (uid?: string) =>
  uid
    ? testEnv.authenticatedContext(uid).firestore()
    : testEnv.unauthenticatedContext().firestore();

beforeAll(async () => {
  testEnv = await initializeTestEnvironment({ projectId, firestore: { rules } });
});
afterEach(async () => testEnv.clearFirestore());
afterAll(async () => testEnv.cleanup());

describe("conversation Firestore rules", () => {
  it("rejects every unauthenticated operation", async () => {
    const conversationRef = doc(database(), "conversations/alice-conversation");
    await assertFails(getDoc(conversationRef));
    await assertFails(setDoc(conversationRef, conversation()));
    await assertFails(updateDoc(conversationRef, { name: "Changed" }));
    await assertFails(deleteDoc(conversationRef));
  });

  it("allows an owner to create, read, update, query, and delete", async () => {
    const alice = database("alice");
    const conversationRef = doc(alice, "conversations/alice-conversation");
    await assertSucceeds(
      setDoc(
        conversationRef,
        conversation("alice", { createdAt: serverTimestamp(), updatedAt: serverTimestamp() })
      )
    );
    await assertSucceeds(getDoc(conversationRef));
    await assertSucceeds(
      getDocs(query(collection(alice, "conversations"), where("userId", "==", "alice")))
    );
    await assertSucceeds(
      updateDoc(conversationRef, {
        name: "Renamed",
        history: [{ type: "user", text: "Updated", sources: [] }],
        isPinned: true,
        updatedAt: serverTimestamp(),
      })
    );
    await assertSucceeds(deleteDoc(conversationRef));
  });

  it("keeps otherwise valid legacy conversations without isPinned usable", async () => {
    const alice = database("alice");
    const conversationRef = doc(alice, "conversations/legacy-conversation");
    const { isPinned: _isPinned, ...legacyConversation } = conversation();

    await assertSucceeds(setDoc(conversationRef, legacyConversation));
    await assertSucceeds(updateDoc(conversationRef, { name: "Renamed legacy conversation" }));
  });

  it("rejects foreign reads, writes, and deletes", async () => {
    await testEnv.withSecurityRulesDisabled(async context => {
      await setDoc(doc(context.firestore(), "conversations/alice-conversation"), conversation());
    });
    const aliceRef = doc(database("bob"), "conversations/alice-conversation");
    await assertFails(getDoc(aliceRef));
    await assertFails(updateDoc(aliceRef, { name: "Bob change" }));
    await assertFails(deleteDoc(aliceRef));
  });

  it("keeps ownership immutable", async () => {
    const alice = database("alice");
    const aliceRef = doc(alice, "conversations/alice-conversation");
    await assertSucceeds(setDoc(aliceRef, conversation()));
    await assertFails(updateDoc(aliceRef, { userId: "bob" }));
    await assertFails(setDoc(doc(alice, "conversations/bob-conversation"), conversation("bob")));
    await assertFails(
      updateDoc(doc(database("bob"), "conversations/alice-conversation"), { userId: "bob" })
    );
  });

  it("rejects invalid schemas and bounded data", async () => {
    const alice = database("alice");
    const ref = (id: string) => doc(alice, `conversations/${id}`);
    await assertFails(setDoc(ref("unknown"), conversation("alice", { injected: true })));
    await assertFails(setDoc(ref("missing-owner"), { ...conversation(), userId: null }));
    await assertFails(setDoc(ref("wrong-type"), conversation("alice", { isPinned: "yes" })));
    await assertFails(setDoc(ref("wrong-name"), conversation("alice", { name: 42 })));
    await assertFails(setDoc(ref("wrong-history"), conversation("alice", { history: "history" })));
    await assertFails(
      setDoc(ref("wrong-timestamp"), conversation("alice", { createdAt: "not-a-timestamp" }))
    );
    await assertFails(setDoc(ref("long-name"), conversation("alice", { name: "a".repeat(121) })));
    await assertFails(
      setDoc(
        ref("too-many"),
        conversation("alice", { history: Array.from({ length: 41 }, () => ({ type: "user" })) })
      )
    );
    await assertSucceeds(
      setDoc(
        ref("boundary"),
        conversation("alice", {
          name: "a".repeat(120),
          history: Array.from({ length: 40 }, () => ({ type: "user" })),
        })
      )
    );
  });
});
