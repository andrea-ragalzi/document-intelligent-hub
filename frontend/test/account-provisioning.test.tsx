import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountProvisioningModal from "@/components/AccountProvisioningModal";

const mocks = vi.hoisted(() => ({
  register: vi.fn(),
}));

vi.mock("@/hooks/useRegistration", () => ({
  useRegistration: () => ({ error: null, isRegistering: false, register: mocks.register }),
}));

describe("first-login account provisioning", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.register.mockResolvedValue("FREE");
  });

  it("completes verified first-login provisioning without an invitation code", async () => {
    const onSuccess = vi.fn();
    render(<AccountProvisioningModal isOpen onSuccess={onSuccess} />);

    expect(screen.queryByLabelText(/invitation code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/invitation code is required/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /continue with free/i }));

    await waitFor(() => {
      expect(mocks.register).toHaveBeenCalledOnce();
      expect(mocks.register).toHaveBeenCalledWith();
      expect(onSuccess).toHaveBeenCalledWith("FREE");
    });
  });
});
