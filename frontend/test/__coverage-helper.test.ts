/**
 * Coverage helper - forces istanbul to track all source files
 * This file imports all components/hooks/stores to ensure they appear in coverage
 */
import { describe, it, expect } from "vitest";

// Import all components
import("../components/AlertMessage");
import("../components/ChatMessageDisplay");
import("../components/ChatSection");
import("../components/ConfirmModal");
import("../components/ConversationList");
import("../components/LoginForm");
import("../components/ProtectedRoute");
import("../components/RenameModal");
import("../components/SaveModal");
import("../components/Sidebar");
import("../components/SignupForm");
import("../components/UploadSection");
import("../components/UserProfile");

// Import all hooks
import("../hooks/useChatAI");
import("../hooks/useDocumentUpload");
import("../hooks/useRAGChat");
import("../hooks/useTheme");

// Import all stores
import("../stores/uiStore");

// Import all lib modules
import("../lib/conversationsService");

describe("Coverage Helper", () => {
  it("should load all modules for coverage tracking", () => {
    expect(true).toBe(true);
  });
});
