/**
 * Custom hook for language flag management
 */

import { useState, useEffect } from "react";
import { getLanguageFlag } from "@/lib/languages";

export function useLanguageFlag(selectedOutputLanguage: string) {
  const [isLanguageSelectorOpen, setIsLanguageSelectorOpen] = useState(false);
  const [languageFlag, setLanguageFlag] = useState<string>("🌍");

  useEffect(() => {
    getLanguageFlag(selectedOutputLanguage).then(setLanguageFlag);
  }, [selectedOutputLanguage]);

  return {
    isLanguageSelectorOpen,
    setIsLanguageSelectorOpen,
    languageFlag,
  };
}
