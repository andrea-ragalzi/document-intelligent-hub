"use client";

import { Globe } from "lucide-react";
import { fetchSupportedLanguages, type Language } from "@/lib/languages";
import { useEffect, useState } from "react";

interface LanguageSelectorProps {
  selectedLanguage: string;
  onLanguageChange: (languageCode: string) => void;
  label?: string;
  disabled?: boolean;
  showNativeNames?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  selectedLanguage,
  onLanguageChange,
  label = "Document Language",
  disabled = false,
  showNativeNames = true,
}) => {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSupportedLanguages()
      .then(setLanguages)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onLanguageChange(e.target.value);
  };

  const getDisplayName = (lang: Language) => {
    if (showNativeNames) {
      return `${lang.flag} ${lang.nativeName} (${lang.name})`;
    }
    return `${lang.flag} ${lang.name}`;
  };

  return (
    <div className="space-y-2">
      <label
        htmlFor="language-selector"
        className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        <Globe size={16} className="text-gray-500 dark:text-gray-400" />
        {label}
      </label>
      <select
        id="language-selector"
        value={selectedLanguage}
        onChange={handleChange}
        disabled={disabled || isLoading}
        className="w-full px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <option>Loading languages...</option>
        ) : (
          languages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {getDisplayName(lang)}
            </option>
          ))
        )}
      </select>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Select the language of your document for better indexing
      </p>
    </div>
  );
};
