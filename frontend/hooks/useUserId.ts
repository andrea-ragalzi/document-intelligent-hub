"use client";

import { useAuth } from "@/contexts/AuthContext";

/**
 * Hook per ottenere l'ID utente corrente da Firebase Auth
 * Ritorna il UID dell'utente autenticato o null se non autenticato
 */
export const useUserId = () => {
  const { user, loading } = useAuth();

  return {
    userId: user?.uid || null,
    isAuthReady: !loading,
  };
};
