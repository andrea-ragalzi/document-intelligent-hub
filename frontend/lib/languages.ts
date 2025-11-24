/**
 * Language Configuration for Document Upload
 *
 * This module provides language utilities and fetches the supported
 * languages from the backend API (single source of truth).
 */

export interface Language {
  code: string;
  name: string; // English name from backend: english_name
  nativeName: string; // Native name from backend: native_name
  flag: string;
}

interface BackendLanguageInfo {
  code: string;
  english_name: string;
  native_name: string;
  flag: string;
  sources_label: string;
}

interface BackendLanguagesResponse {
  languages: BackendLanguageInfo[];
  total_count: number;
}

/**
 * Cached languages fetched from backend API
 */
let cachedLanguages: Language[] | null = null;

/**
 * Fetch supported languages from backend API
 * Returns cached result on subsequent calls (languages rarely change)
 */
export async function fetchSupportedLanguages(): Promise<Language[]> {
  // Return cached result if available
  if (cachedLanguages !== null) {
    return cachedLanguages;
  }

  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(
      "/rag",
      ""
    );
    const response = await fetch(`${apiBaseUrl}/rag/languages/`, {
      cache: "force-cache", // Cache indefinitely (languages rarely change)
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch languages: ${response.status}`);
    }

    const data: BackendLanguagesResponse = await response.json();

    // Transform backend format to frontend format
    cachedLanguages = data.languages.map((lang: BackendLanguageInfo) => ({
      code: lang.code.toLowerCase(), // Backend uses uppercase, frontend uses lowercase
      name: lang.english_name,
      nativeName: lang.native_name,
      flag: lang.flag,
    }));

    return cachedLanguages;
  } catch (error) {
    // Silently handle network errors (server offline)
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.log("⚠️ Server offline - using fallback languages");
    } else {
      console.error("Error fetching supported languages:", error);
    }

    // Fallback to minimal language set if API fails
    const fallback = [
      { code: "en", name: "English", nativeName: "English", flag: "🇬🇧" },
      { code: "it", name: "Italian", nativeName: "Italiano", flag: "🇮🇹" },
      { code: "es", name: "Spanish", nativeName: "Español", flag: "🇪🇸" },
    ];

    cachedLanguages = fallback;
    return fallback;
  }
}

/**
 * Get language by code (requires languages to be fetched first)
 */
export async function getLanguageByCode(
  code: string
): Promise<Language | undefined> {
  const languages = await fetchSupportedLanguages();
  return languages.find((lang) => lang.code === code.toLowerCase());
}

/**
 * Get language flag emoji by code
 */
export async function getLanguageFlag(code: string): Promise<string> {
  const lang = await getLanguageByCode(code);
  return lang?.flag || "🌍";
}

/**
 * Get language display name
 */
export async function getLanguageName(code: string): Promise<string> {
  const lang = await getLanguageByCode(code);
  return lang ? `${lang.nativeName} (${lang.name})` : code.toUpperCase();
}
