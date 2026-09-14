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
    const result = await signInAnonymously(getFirebaseAuth());
    return result.user;
  } catch (error) {
    console.error("Anonymous sign-in failed.");
    throw error;
  }
}

/**
 * Sign in with email and password
 */
export async function signInWithEmail(email: string, password: string): Promise<User> {
  try {
    const result = await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
    return result.user;
  } catch (error) {
    console.error("Email sign-in failed.");
    throw error;
  }
}

/**
 * Create new user with email and password
 */
export async function signUpWithEmail(email: string, password: string): Promise<User> {
  try {
    const result = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
    return result.user;
  } catch (error) {
    console.error("Account creation failed.");
    throw error;
  }
}

/**
 * Sign out current user
 */
export async function signOut(): Promise<void> {
  try {
    await firebaseSignOut(getFirebaseAuth());
  } catch (error) {
    console.error("Sign-out failed.");
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
