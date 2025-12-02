import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useUIStore } from "../../stores/uiStore";

describe("useUIStore", () => {
  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useUIStore());
    act(() => {
      result.current.resetConversation();
      result.current.closeRenameModal();
      result.current.closeDeleteModal();
      result.current.setStatusAlert(null);
    });
  });

  describe("Status Alert Management", () => {
    it("should set and clear status alert", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setStatusAlert({
          message: "Test alert",
          type: "success",
        });
      });

      expect(result.current.statusAlert).toEqual({
        message: "Test alert",
        type: "success",
      });

      act(() => {
        result.current.setStatusAlert(null);
      });

      expect(result.current.statusAlert).toBeNull();
    });

    it("should handle different alert types", () => {
      const { result } = renderHook(() => useUIStore());

      const alertTypes: Array<"success" | "error" | "info"> = ["success", "error", "info"];

      alertTypes.forEach(type => {
        act(() => {
          result.current.setStatusAlert({
            message: `${type} message`,
            type,
          });
        });

        expect(result.current.statusAlert?.type).toBe(type);
      });
    });
  });

  describe("Rename Modal Management", () => {
    it("should open rename modal with conversation details", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.openRenameModal("conv-123", "Old Name");
      });

      expect(result.current.renameModalOpen).toBe(true);
      expect(result.current.conversationToRename).toEqual({
        id: "conv-123",
        currentName: "Old Name",
      });
    });

    it("should close rename modal and clear conversation", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.openRenameModal("conv-123", "Old Name");
      });

      expect(result.current.renameModalOpen).toBe(true);

      act(() => {
        result.current.closeRenameModal();
      });

      expect(result.current.renameModalOpen).toBe(false);
      expect(result.current.conversationToRename).toBeNull();
    });
  });

  describe("Delete Modal Management", () => {
    it("should open delete modal with conversation details", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.openDeleteModal("conv-456", "Conversation to Delete");
      });

      expect(result.current.confirmDeleteOpen).toBe(true);
      expect(result.current.conversationToDelete).toEqual({
        id: "conv-456",
        name: "Conversation to Delete",
      });
    });

    it("should close delete modal and clear conversation", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.openDeleteModal("conv-456", "Test");
      });

      expect(result.current.confirmDeleteOpen).toBe(true);

      act(() => {
        result.current.closeDeleteModal();
      });

      expect(result.current.confirmDeleteOpen).toBe(false);
      expect(result.current.conversationToDelete).toBeNull();
    });
  });

  describe("Conversation Tracking", () => {
    it("should set current conversation ID", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setCurrentConversation("conv-789");
      });

      expect(result.current.currentConversationId).toBe("conv-789");
    });

    it("should update saved message count", () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.updateSavedMessageCount(10);
      });

      expect(result.current.lastSavedMessageCount).toBe(10);
    });

    it("should track saving state", () => {
      const { result } = renderHook(() => useUIStore());

      expect(result.current.isSaving).toBe(false);

      act(() => {
        result.current.startSaving();
      });

      expect(result.current.isSaving).toBe(true);

      act(() => {
        result.current.finishSaving();
      });

      expect(result.current.isSaving).toBe(false);
    });

    it("should reset conversation state completely", () => {
      const { result } = renderHook(() => useUIStore());

      // Set some state
      act(() => {
        result.current.setCurrentConversation("conv-999");
        result.current.updateSavedMessageCount(20);
      });

      expect(result.current.currentConversationId).toBe("conv-999");
      expect(result.current.lastSavedMessageCount).toBe(20);

      // Reset
      act(() => {
        result.current.resetConversation();
      });

      expect(result.current.currentConversationId).toBeNull();
      expect(result.current.lastSavedMessageCount).toBe(0);
    });
  });

  describe("Complex Workflows", () => {
    it("should handle complete conversation lifecycle", () => {
      const { result } = renderHook(() => useUIStore());

      // Start new conversation
      act(() => {
        result.current.resetConversation();
      });

      expect(result.current.currentConversationId).toBeNull();
      expect(result.current.lastSavedMessageCount).toBe(0);

      // Simulate saving
      act(() => {
        result.current.startSaving();
        result.current.setCurrentConversation("new-conv-id");
        result.current.updateSavedMessageCount(2);
        result.current.finishSaving();
      });

      expect(result.current.currentConversationId).toBe("new-conv-id");
      expect(result.current.lastSavedMessageCount).toBe(2);
      expect(result.current.isSaving).toBe(false);

      // Update with more messages
      act(() => {
        result.current.startSaving();
        result.current.updateSavedMessageCount(4);
        result.current.finishSaving();
      });

      expect(result.current.lastSavedMessageCount).toBe(4);

      // Delete conversation
      act(() => {
        result.current.openDeleteModal("new-conv-id", "Test Conversation");
      });

      expect(result.current.confirmDeleteOpen).toBe(true);

      act(() => {
        result.current.resetConversation();
        result.current.closeDeleteModal();
      });

      expect(result.current.currentConversationId).toBeNull();
      expect(result.current.lastSavedMessageCount).toBe(0);
      expect(result.current.confirmDeleteOpen).toBe(false);
    });
  });
});
