"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendEmailVerification,
  signOut,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
} from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<{ verificationEmailSent: boolean }>;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
  emailVerified: boolean;
  sendVerificationEmail: () => Promise<void>;
  refreshEmailVerification: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [emailVerified, setEmailVerified] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("🔐 Setting up auth state listener...");

    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), user => {
      console.log("🔐 Auth state changed:", user ? user.uid : "No user - auth required");
      setUser(user);
      setEmailVerified(Boolean(user?.emailVerified));
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
  };

  const signUp = async (email: string, password: string) => {
    const credential = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
    setUser(credential.user);
    setEmailVerified(Boolean(credential.user.emailVerified));
    try {
      await sendEmailVerification(credential.user);
      return { verificationEmailSent: true };
    } catch {
      return { verificationEmailSent: false };
    }
  };

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider();
    await signInWithPopup(getFirebaseAuth(), provider);
  };

  const logout = async () => {
    await signOut(getFirebaseAuth());
    setEmailVerified(false);
  };

  const getIdToken = async (): Promise<string | null> => {
    if (!user) return null;
    return await user.getIdToken();
  };

  const sendVerificationEmail = async (): Promise<void> => {
    if (!user) {
      throw new Error("No authenticated user");
    }
    await sendEmailVerification(user);
  };

  const refreshEmailVerification = async (): Promise<boolean> => {
    if (!user) {
      return false;
    }

    await user.reload();
    await user.getIdToken(true);
    const verified = Boolean(user.emailVerified);
    setEmailVerified(verified);
    return verified;
  };

  const value: AuthContextType = {
    user,
    loading,
    signIn,
    signUp,
    signInWithGoogle,
    logout,
    getIdToken,
    emailVerified,
    sendVerificationEmail,
    refreshEmailVerification,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
