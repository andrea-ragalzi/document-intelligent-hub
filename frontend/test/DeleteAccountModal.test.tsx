import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DeleteAccountModal } from "@/components/DeleteAccountModal";

describe("DeleteAccountModal", () => {
  it("requires the current password and displays a deletion failure", async () => {
    const onConfirm = vi
      .fn()
      .mockRejectedValue(new Error("The password is incorrect. Please try again."));

    render(
      <DeleteAccountModal
        isOpen
        onClose={vi.fn()}
        onConfirm={onConfirm}
        userEmail="user@example.com"
        requiresPassword
      />
    );

    fireEvent.change(screen.getByLabelText(/type delete to confirm/i), {
      target: { value: "DELETE" },
    });
    expect(screen.getByRole("button", { name: /delete account/i })).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/confirm your password/i), {
      target: { value: "incorrect-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /delete account/i }));

    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith("incorrect-password"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The password is incorrect. Please try again."
    );
  });
});
