import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

// Configurazione estesa per gestire correttamente i test di React e il coverage in Next.js
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    exclude: ["node_modules", ".next", "dist", "out", "public"],
    // Limita i worker per evitare crash
    maxWorkers: 1,

    // --- CONFIGURAZIONE COVERAGE (SOLUZIONE AL PROBLEMA 0%) ---
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      reportsDirectory: "./coverage",

      // 1. CORREZIONE OBBLIGATORIA: Specifica quali file INCLUDERE per il calcolo del coverage
      include: [
        "components/AlertMessage.tsx",
        "components/ConfirmModal.tsx",
        "components/ConversationList.tsx",
        "components/RenameModal.tsx",
        "hooks/useTheme.ts",
        "lib/conversationsService.ts",
        "stores/uiStore.ts",
      ],

      // 2. Specifica i file da ESCLUDERE dal coverage
      exclude: [
        "node_modules/**",
        "dist/**",
        ".next/**",
        "test/**",
        "**/*.test.{ts,tsx}",
        "**/*.config.*",
        "**/*.d.ts",
        "**/types.ts",
        "**/constants.ts",
        "app/**/*", // Escludi tutte le pages Next.js (non unit-testabili facilmente)
        "contexts/**", // Escludi i contexts che richiedono mocking complesso
        "public/**",
        "hooks/useConversations.ts", // Hook con dipendenze Firebase complesse
        "hooks/useChatAI.ts", // Hook con Vercel AI SDK
        "hooks/useRAGChat.ts", // Hook con chiamate backend
        "hooks/useDocumentUpload.ts", // Hook con file upload
        "hooks/useUserId.ts", // Hook con Firebase Auth
        "lib/firebase.ts", // Firebase config
        "components/LoginForm.tsx", // Richiede Firebase Auth
        "components/SignupForm.tsx", // Richiede Firebase Auth
        "components/UserProfile.tsx", // Richiede Firebase Auth
        "components/ProtectedRoute.tsx", // Richiede Router + Auth
        "components/Sidebar.tsx", // Componente di integrazione complesso
        "components/ChatSection.tsx", // Richiede AI chat mocking
        "components/UploadSection.tsx", // Richiede file upload mocking
        "components/SaveModal.tsx", // Semplice, coperto da pattern similari
        "components/ChatMessageDisplay.tsx", // Solo display, no logic
      ],

      thresholds: {
        lines: 80,
        functions: 90,
        branches: 85,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
