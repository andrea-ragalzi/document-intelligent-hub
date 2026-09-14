// Costanti dell'applicazione

// API Base URL - usa variabile d'ambiente o fallback a localhost
// Per accesso da mobile, imposta NEXT_PUBLIC_API_BASE_URL con l'IP locale del PC
// Es: NEXT_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/rag
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/rag";

/** Public-demo upload limit enforced again by the backend. */
export const MAX_UPLOAD_SIZE_MB = 10;
export const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;

export const CONVERSATIONS_KEY = "rag_conversations";
