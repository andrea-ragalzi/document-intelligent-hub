/**
 * Coverage helper - forces istanbul to track all source files
 * This file imports all components/hooks/stores to ensure they appear in coverage
 */
import { describe, it, expect } from "vitest";

describe("Coverage Helper", () => {
  it("should load all modules for coverage tracking", async () => {
    const modules = await Promise.all([
      // Components
      import("../components/AlertMessage"),
      import("../components/ChatMessageDisplay"),
      import("../components/ChatSection"),
      import("../components/ConfirmModal"),
      import("../components/ConversationList"),
      import("../components/LoginForm"),
      import("../components/ProtectedRoute"),
      import("../components/RenameModal"),
      import("../components/SaveModal"),
      import("../components/Sidebar"),
      import("../components/SignupForm"),
      import("../components/UploadSection"),
      import("../components/UserProfile"),
      // Hooks
      import("../hooks/useChatAI"),
      import("../hooks/useDocumentUpload"),
      import("../hooks/useRAGChat"),
      import("../hooks/useTheme"),
      // Stores and libraries
      import("../stores/uiStore"),
      import("../lib/conversationsService"),
    ]);

    expect(modules).toHaveLength(19);
  });
});
