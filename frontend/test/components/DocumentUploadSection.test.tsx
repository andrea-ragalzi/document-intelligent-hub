import { fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import { DocumentUploadSection } from "@/components/DocumentModal/DocumentUploadSection";

const renderUploadSection = () => {
  const fileInputRef = createRef<HTMLInputElement>();

  render(
    <DocumentUploadSection
      file={null}
      isUploading={false}
      userId="test-user"
      dragActive={false}
      uploadAlert={{ message: "", type: "info" }}
      statusAlert={null}
      fileInputRef={fileInputRef}
      onFileChange={vi.fn()}
      onUpload={vi.fn()}
      onDragEnter={vi.fn()}
      onDragLeave={vi.fn()}
      onDragOver={vi.fn()}
      onDrop={vi.fn()}
    />
  );

  return fileInputRef;
};

describe("DocumentUploadSection", () => {
  it.each(["Enter", " "])("opens the file picker with the %j key", key => {
    const fileInputRef = renderUploadSection();
    const clickSpy = vi.spyOn(fileInputRef.current as HTMLInputElement, "click");

    fireEvent.keyDown(screen.getByRole("button", { name: /drag & drop pdf/i }), {
      key,
    });

    expect(clickSpy).toHaveBeenCalledOnce();
  });
});
