import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import DocumentList, { type Document } from "@/components/DocumentList";
import type { ComponentProps } from "react";

describe("DocumentList", () => {
  const mockDocuments: Document[] = [
    {
      filename: "alpha.pdf",
      chunks_count: 12,
      language: "en",
    },
    {
      filename: "beta.pdf",
      chunks_count: 8,
      language: "it",
    },
  ];

  const renderComponent = (
    props?: Partial<ComponentProps<typeof DocumentList>>
  ) => {
    const onDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        deletingDoc={null}
        onDelete={onDelete}
        {...props}
      />
    );

    return { onDelete };
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("opens the context menu and confirms deletion before the menu closes", async () => {
    const { onDelete } = renderComponent();

    const optionsButtons = screen.getAllByTitle("Options");
    fireEvent.click(optionsButtons[0]);

    const deleteMenuButton = await screen.findByRole("button", {
      name: "Delete",
    });
    fireEvent.click(deleteMenuButton);

    expect(await screen.findByText("Delete document?")).toBeInTheDocument();
    expect(screen.getAllByText(mockDocuments[0].filename)).toHaveLength(2);

    const confirmDeleteButton = screen.getByRole("button", { name: "Delete" });
    fireEvent.click(confirmDeleteButton);

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith(mockDocuments[0].filename);
    });
  });

  it("keeps the menu open when pressing inside an action button", async () => {
    renderComponent();

    const optionsButtons = screen.getAllByTitle("Options");
    fireEvent.click(optionsButtons[0]);

    const deleteMenuButton = await screen.findByRole("button", {
      name: "Delete",
    });

    fireEvent.mouseDown(deleteMenuButton);

    expect(
      screen.getByRole("button", {
        name: "Delete",
      })
    ).toBeInTheDocument();
  });
});
