// Costanti dell'applicazione

// API Base URL - usa variabile d'ambiente o fallback a localhost
// Per accesso da mobile, imposta NEXT_PUBLIC_API_BASE_URL con l'IP locale del PC
// Es: NEXT_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/rag
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/rag";

export const CONVERSATIONS_KEY = "rag_conversations";
