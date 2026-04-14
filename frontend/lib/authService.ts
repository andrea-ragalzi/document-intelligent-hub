/**
 * Firebase Authentication Service
 * Handles anonymous and email/password authentication
 */

import {
  signInAnonymously,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
} from "firebase/auth";
import { getFirebaseAuth } from "./firebase";

/**
 * Sign in anonymously for development/demo purposes
 */
export async function signInAnonymous(): Promise<User> {
  try {
    console.log("🔐 Signing in anonymously...");
    const result = await signInAnonymously(getFirebaseAuth());
    console.log("✅ Anonymous sign-in successful:", result.user.uid);
    return result.user;
  } catch (error) {
    console.error("❌ Anonymous sign-in failed:", error);
    throw error;
  }
}

/**
 * Sign in with email and password
 */
export async function signInWithEmail(email: string, password: string): Promise<User> {
  try {
    console.log("🔐 Signing in with email...");
    const result = await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
    console.log("✅ Email sign-in successful:", result.user.uid);
    return result.user;
  } catch (error) {
    console.error("❌ Email sign-in failed:", error);
    throw error;
  }
}

/**
 * Create new user with email and password
 */
export async function signUpWithEmail(email: string, password: string): Promise<User> {
  try {
    console.log("🔐 Creating new user...");
    const result = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
    console.log("✅ User created successfully:", result.user.uid);
    return result.user;
  } catch (error) {
    console.error("❌ User creation failed:", error);
    throw error;
  }
}

/**
 * Sign out current user
 */
export async function signOut(): Promise<void> {
  try {
    console.log("🔐 Signing out...");
    await firebaseSignOut(getFirebaseAuth());
    console.log("✅ Sign-out successful");
  } catch (error) {
    console.error("❌ Sign-out failed:", error);
    throw error;
  }
}

/**
 * Get current authenticated user
 */
export function getCurrentUser(): User | null {
  return getFirebaseAuth().currentUser;
}

/**
 * Listen to authentication state changes
 */
export function onAuthChange(callback: (user: User | null) => void): () => void {
  return onAuthStateChanged(getFirebaseAuth(), callback);
}

/**
 * Get current user ID (wait for auth to be ready)
 */
export async function getCurrentUserId(): Promise<string> {
  return new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), user => {
      unsubscribe();
      if (user) {
        resolve(user.uid);
      } else {
        reject(new Error("No authenticated user"));
      }
    });
  });
}
