import { API_BASE_URL } from "./constants";

/** Delete server-side account data before Firebase Auth deletes the identity. */
export async function deleteAccountData(idToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/account/data`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${idToken}` },
  });

  if (!response.ok) {
    throw new Error("Unable to delete account data");
  }
}
