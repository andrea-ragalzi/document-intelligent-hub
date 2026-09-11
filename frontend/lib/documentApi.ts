import { API_BASE_URL } from "@/lib/constants";

/** Fetch a private indexed document through the authenticated backend boundary. */
export async function fetchDocumentContent(
  filename: string,
  token: string,
  download = false
): Promise<Blob> {
  const query = new URLSearchParams({ filename });
  if (download) query.set("download", "true");

  const response = await fetch(`${API_BASE_URL}/documents/content?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("Document content request failed");
  }
  return response.blob();
}
