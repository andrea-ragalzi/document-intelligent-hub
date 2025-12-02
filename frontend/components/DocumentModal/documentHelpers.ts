/**
 * Helper functions for DocumentModal component
 */

/**
 * Formats a date string to Italian locale format
 */
export function formatDate(dateString?: string): string {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
}

/**
 * Creates a synthetic file change event for drag-and-drop
 */
export function createFileChangeEvent(
  file: File,
  inputRef: React.RefObject<HTMLInputElement | null>
): void {
  if (!inputRef.current) return;

  const dt = new DataTransfer();
  dt.items.add(file);
  inputRef.current.files = dt.files;
  const event = new Event("change", { bubbles: true });
  inputRef.current.dispatchEvent(event);
}

/**
 * Validates if a file is a PDF
 */
export function isPdfFile(file: File): boolean {
  return file.type === "application/pdf";
}
