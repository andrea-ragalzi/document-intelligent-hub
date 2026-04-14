"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
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
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("🔐 Setting up auth state listener...");

    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), user => {
      console.log("🔐 Auth state changed:", user ? user.uid : "No user - auth required");
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
  };

  const signUp = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
  };

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider();
    await signInWithPopup(getFirebaseAuth(), provider);
  };

  const logout = async () => {
    await signOut(getFirebaseAuth());
  };

  const getIdToken = async (): Promise<string | null> => {
    if (!user) return null;
    return await user.getIdToken();
  };

  const value: AuthContextType = {
    user,
    loading,
    signIn,
    signUp,
    signInWithGoogle,
    logout,
    getIdToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
