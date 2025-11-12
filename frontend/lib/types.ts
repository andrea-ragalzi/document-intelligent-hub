// Tipi e interfacce per l'applicazione RAG

export interface ChatMessage {
  type: "user" | "assistant";
  text: string;
  sources: string[];
  isThinking?: boolean;
}

export interface SavedConversation {
  id: string;
  userId?: string; // Optional for backward compatibility with localStorage
  name: string;
  timestamp: string;
  history: ChatMessage[];
}

export interface AlertState {
  message: string;
  type: "success" | "error" | "info";
}

export type Theme = "light" | "dark";
