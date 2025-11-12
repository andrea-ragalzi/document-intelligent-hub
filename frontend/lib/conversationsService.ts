/**
 * Firestore Conversations Service
 * Manages saving and loading conversations to/from Firebase Firestore
 */

import {
  collection,
  addDoc,
  getDocs,
  deleteDoc,
  updateDoc,
  doc,
  query,
  where,
  // orderBy, // Temporarily commented until we create the index
  Timestamp,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "./firebase";
import type { SavedConversation, ChatMessage } from "./types";

const CONVERSATIONS_COLLECTION = "conversations";

/**
 * Save a new conversation to Firestore
 */
export async function saveConversationToFirestore(
  userId: string,
  name: string,
  history: ChatMessage[]
): Promise<SavedConversation> {
  console.log("🔥 saveConversationToFirestore called");
  console.log("  userId:", userId);
  console.log("  name:", name);
  console.log("  history length:", history.length);

  try {
    const conversationData = {
      userId,
      name,
      history,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    };

    console.log("📤 Adding document to Firestore...");
    console.log("  Collection:", CONVERSATIONS_COLLECTION);
    console.log("  Database:", db);
    console.log("  ConversationData:", {
      userId,
      name,
      historyLength: history.length,
    });

    try {
      const collectionRef = collection(db, CONVERSATIONS_COLLECTION);
      console.log("  Collection reference:", collectionRef);

      const docRef = await addDoc(collectionRef, conversationData);
      console.log("✅ Document added with ID:", docRef.id);

      return {
        id: docRef.id,
        userId,
        name,
        timestamp: new Date().toLocaleString("en-US"),
        history,
      };
    } catch (addError: unknown) {
      console.error("❌ Firestore addDoc error:", addError);
      if (addError instanceof Error) {
        console.error("❌ Error message:", addError.message);
        console.error("❌ Error stack:", addError.stack);
      }
      const errorObj = addError as { code?: string };
      console.error("❌ Error code:", errorObj?.code);
      throw addError;
    }
  } catch (error) {
    console.error("❌ Error saving conversation to Firestore:", error);
    throw new Error("Failed to save conversation");
  }
}

/**
 * Load all conversations for a user from Firestore
 */
export async function loadConversationsFromFirestore(
  userId: string
): Promise<SavedConversation[]> {
  console.log("📥 Loading conversations from Firestore for user:", userId);

  try {
    // Simplified query without orderBy to avoid index requirement
    // TODO: Add orderBy when index is created
    const q = query(
      collection(db, CONVERSATIONS_COLLECTION),
      where("userId", "==", userId)
      // orderBy("createdAt", "desc") // Temporarily commented
    );

    console.log("  Executing query...");
    const querySnapshot = await getDocs(q);
    const conversations: SavedConversation[] = [];

    querySnapshot.forEach((doc) => {
      const data = doc.data();
      conversations.push({
        id: doc.id,
        userId: data.userId,
        name: data.name,
        timestamp: data.createdAt
          ? (data.createdAt as Timestamp).toDate().toLocaleString("en-US")
          : new Date().toLocaleString("en-US"),
        history: data.history,
      });
    });

    // Sort manually in memory for now
    conversations.sort((a, b) => {
      // Sort by timestamp descending (most recent first)
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });

    console.log("✅ Loaded", conversations.length, "conversations");
    return conversations;
  } catch (error) {
    console.error("❌ Error loading conversations from Firestore:", error);
    throw new Error("Failed to load conversations");
  }
}

/**
 * Delete a conversation from Firestore
 */
export async function deleteConversationFromFirestore(
  conversationId: string
): Promise<void> {
  try {
    await deleteDoc(doc(db, CONVERSATIONS_COLLECTION, conversationId));
  } catch (error) {
    console.error("Error deleting conversation from Firestore:", error);
    throw new Error("Failed to delete conversation");
  }
}

/**
 * Update the name of a conversation in Firestore
 */
export async function updateConversationNameInFirestore(
  conversationId: string,
  newName: string
): Promise<void> {
  console.log("✏️ Updating conversation name in Firestore");
  console.log("  ID:", conversationId);
  console.log("  New name:", newName);

  try {
    const conversationRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
    await updateDoc(conversationRef, {
      name: newName,
      updatedAt: serverTimestamp(),
    });
    console.log("✅ Conversation name updated successfully");
  } catch (error) {
    console.error("❌ Error updating conversation name:", error);
    throw new Error("Failed to update conversation name");
  }
}

/**
 * Update the content (history) of a conversation in Firestore
 */
export async function updateConversationHistoryInFirestore(
  conversationId: string,
  history: ChatMessage[]
): Promise<void> {
  console.log("📝 Updating conversation history in Firestore");
  console.log("  ID:", conversationId);
  console.log("  Messages:", history.length);

  try {
    const conversationRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
    await updateDoc(conversationRef, {
      history,
      updatedAt: serverTimestamp(),
    });
    console.log("✅ Conversation history updated successfully");
  } catch (error) {
    console.error("❌ Error updating conversation history:", error);
    throw new Error("Failed to update conversation history");
  }
}

/**
 * Sync conversations from localStorage to Firestore
 * Useful for migrating existing data
 */
export async function migrateLocalStorageToFirestore(
  userId: string,
  localConversations: SavedConversation[]
): Promise<void> {
  try {
    const promises = localConversations.map((conv) =>
      saveConversationToFirestore(userId, conv.name, conv.history)
    );
    await Promise.all(promises);
    console.log(
      `Successfully migrated ${localConversations.length} conversations to Firestore`
    );
  } catch (error) {
    console.error("Error migrating conversations to Firestore:", error);
    throw new Error("Failed to migrate conversations");
  }
}
