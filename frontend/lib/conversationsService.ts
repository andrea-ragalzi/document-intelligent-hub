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
import { getFirebaseAuth, getFirebaseDb } from "./firebase";
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
  try {
    // Verify authentication
    const currentUser = getFirebaseAuth().currentUser;
    if (!currentUser) {
      throw new Error("User must be authenticated to save conversations");
    }
    if (currentUser.uid !== userId) {
      throw new Error("UserId does not match authenticated user");
    }

    const conversationData = {
      userId,
      name,
      history,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      isPinned: false, // Initialize isPinned to false for new conversations
    };

    try {
      const collectionRef = collection(getFirebaseDb(), CONVERSATIONS_COLLECTION);
      const docRef = await addDoc(collectionRef, conversationData);

      // Format timestamp without comma
      const now = new Date();
      const formattedDate = now.toLocaleDateString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
      const formattedTime = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const timestamp = `${formattedDate} ${formattedTime}`;

      return {
        id: docRef.id,
        userId,
        name,
        timestamp,
        history,
        isPinned: false, // Initialize isPinned for return value
      };
    } catch (addError: unknown) {
      console.error("Unable to create conversation.");
      throw addError;
    }
  } catch {
    console.error("Unable to save conversation.");
    throw new Error("Failed to save conversation");
  }
}

/**
 * Load all conversations for a user from Firestore
 */
export async function loadConversationsFromFirestore(userId: string): Promise<SavedConversation[]> {
  try {
    // Simplified query without orderBy to avoid index requirement
    // TODO: Add orderBy when index is created
    const q = query(
      collection(getFirebaseDb(), CONVERSATIONS_COLLECTION),
      where("userId", "==", userId)
      // orderBy("createdAt", "desc") // Temporarily commented
    );

    const querySnapshot = await getDocs(q);
    const conversations: SavedConversation[] = [];

    querySnapshot.forEach(doc => {
      const data = doc.data();
      const isPinned = data.isPinned || false;

      // Format timestamp without comma
      const date = data.createdAt ? (data.createdAt as Timestamp).toDate() : new Date();
      const formattedDate = date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
      const formattedTime = date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const timestamp = `${formattedDate} ${formattedTime}`;

      conversations.push({
        id: doc.id,
        userId: data.userId,
        name: data.name,
        timestamp,
        history: data.history,
        isPinned, // Include isPinned field
      });
    });

    // Sort manually in memory for now
    conversations.sort((a, b) => {
      // Sort by timestamp descending (most recent first)
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });

    return conversations;
  } catch {
    console.error("Unable to load conversations.");
    throw new Error("Failed to load conversations");
  }
}

/**
 * Delete a conversation from Firestore
 */
export async function deleteConversationFromFirestore(conversationId: string): Promise<void> {
  try {
    await deleteDoc(doc(getFirebaseDb(), CONVERSATIONS_COLLECTION, conversationId));
  } catch {
    console.error("Unable to delete conversation.");
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
  try {
    const conversationRef = doc(getFirebaseDb(), CONVERSATIONS_COLLECTION, conversationId);
    await updateDoc(conversationRef, {
      name: newName,
      updatedAt: serverTimestamp(),
    });
  } catch {
    console.error("Unable to rename conversation.");
    throw new Error("Failed to update conversation name");
  }
}

/**
 * Update the content (history) of a conversation in Firestore
 */
export async function updateConversationHistoryInFirestore(
  conversationId: string,
  history: ChatMessage[],
  metadata?: { isPinned?: boolean }
): Promise<void> {
  // Don't try to update temporary conversations
  if (conversationId.startsWith("temp-")) {
    return;
  }

  try {
    // Check authentication status
    const currentUser = getFirebaseAuth().currentUser;
    if (!currentUser) {
      throw new Error("User must be authenticated to update conversations");
    }

    const conversationRef = doc(getFirebaseDb(), CONVERSATIONS_COLLECTION, conversationId);
    const updateData: {
      history: ChatMessage[];
      updatedAt: ReturnType<typeof serverTimestamp>;
      isPinned?: boolean;
    } = {
      history,
      updatedAt: serverTimestamp(),
    };

    // Add metadata fields if provided
    if (metadata?.isPinned !== undefined) {
      updateData.isPinned = metadata.isPinned;
    }
    await updateDoc(conversationRef, updateData);
  } catch {
    console.error("Unable to update conversation history.");
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
    const promises = localConversations.map(conv =>
      saveConversationToFirestore(userId, conv.name, conv.history)
    );
    await Promise.all(promises);
  } catch {
    console.error("Unable to migrate conversations.");
    throw new Error("Failed to migrate conversations");
  }
}
