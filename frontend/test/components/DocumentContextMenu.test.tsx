import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DocumentContextMenu } from "@/components/DocumentList/DocumentContextMenu";

describe("DocumentContextMenu", () => {
  it("offers preview, download, and delete for the selected document", () => {
    const onPreview = vi.fn();
    const onDownload = vi.fn();
    const onDelete = vi.fn();
    const runActionAndCloseMenu = (action: () => void) => action();

    render(
      <DocumentContextMenu
        isOpen={true}
        menuPosition={{ top: 20, right: 20 }}
        dragY={0}
        isDragging={false}
        selectedDoc="private.pdf"
        originalAvailable={true}
        menuRef={{ current: null }}
        onClose={vi.fn()}
        onPreview={onPreview}
        onDownload={onDownload}
        onDelete={onDelete}
        onDragStart={vi.fn()}
        onDragMove={vi.fn()}
        onDragEnd={vi.fn()}
        runActionAndCloseMenu={runActionAndCloseMenu}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Preview document" }));
    fireEvent.click(screen.getByRole("button", { name: "Download document" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete document" }));

    expect(onPreview).toHaveBeenCalledWith("private.pdf");
    expect(onDownload).toHaveBeenCalledWith("private.pdf");
    expect(onDelete).toHaveBeenCalledWith("private.pdf");
  });

  it("disables preview and download when the original is unavailable", () => {
    render(
      <DocumentContextMenu
        isOpen={true}
        menuPosition={{ top: 20, right: 20 }}
        dragY={0}
        isDragging={false}
        selectedDoc="older-document.pdf"
        originalAvailable={false}
        menuRef={{ current: null }}
        onClose={vi.fn()}
        onPreview={vi.fn()}
        onDownload={vi.fn()}
        onDelete={vi.fn()}
        onDragStart={vi.fn()}
        onDragMove={vi.fn()}
        onDragEnd={vi.fn()}
        runActionAndCloseMenu={action => action()}
      />
    );

    expect(screen.getByRole("button", { name: "Preview document" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Download document" })).toBeDisabled();
  });
});
