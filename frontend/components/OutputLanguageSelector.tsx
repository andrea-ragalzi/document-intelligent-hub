import { createPortal } from "react-dom";
import { useState, useRef, useEffect } from "react";
import { fetchSupportedLanguages, type Language } from "@/lib/languages";

interface OutputLanguageSelectorProps {
  isOpen: boolean;
  selectedLanguageCode: string;
  onSelectLanguage: (code: string) => void;
  onClose: () => void;
}

export const OutputLanguageSelector: React.FC<OutputLanguageSelectorProps> = ({
  isOpen,
  selectedLanguageCode,
  onSelectLanguage,
  onClose,
}) => {
  const [dragY, setDragY] = useState(0);
  const dragStartY = useRef(0);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSupportedLanguages()
      .then(setLanguages)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (!isOpen) return null;

  const handleLanguageClick = (code: string) => {
    onSelectLanguage(code);
    onClose();
  };

  const handleDragStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    dragStartY.current = touch.clientY;
  };

  const handleDragMove = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    const deltaY = Math.max(0, touch.clientY - dragStartY.current);
    setDragY(deltaY);
  };

  const handleDragEnd = () => {
    if (dragY > 100) {
      onClose();
    }
    setDragY(0);
  };

  return createPortal(
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/90 z-[100]"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
      />

      {/* Mobile Bottom Sheet */}
      <div className="fixed inset-0 z-[110] flex items-end justify-center pt-20">
        <div
          className="bg-white dark:bg-gray-800 rounded-t-3xl shadow-2xl w-full overflow-hidden flex flex-col transition-transform"
          style={{
            maxHeight: "calc(100vh - 5rem)",
            transform: `translateY(${dragY}px)`,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Drag Handle */}
          <div
            className="flex justify-center pt-4 pb-2 bg-white dark:bg-gray-800 cursor-grab active:cursor-grabbing"
            onTouchStart={handleDragStart}
            onTouchMove={handleDragMove}
            onTouchEnd={handleDragEnd}
          >
            <div className="w-10 h-1 bg-gray-300 dark:bg-gray-600 rounded-full" />
          </div>

          {/* Title */}
          <div className="px-4 py-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Select Response Language
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Choose the language for AI responses
            </p>
          </div>

          {/* Languages List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-gray-500 dark:text-gray-400">
                  Loading languages...
                </div>
              </div>
            ) : (
              languages.map((language: Language) => {
                const isSelected = selectedLanguageCode === language.code;

                return (
                  <button
                    key={language.code}
                    onClick={() => handleLanguageClick(language.code)}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                      isSelected
                        ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-500"
                        : "bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600 hover:bg-indigo-50/50 dark:hover:bg-gray-600"
                    }`}
                  >
                    {/* Flag */}
                    <div className="flex-shrink-0 text-2xl">
                      {language.flag}
                    </div>

                    {/* Language Names */}
                    <div className="flex-1">
                      <h3
                        className={`text-base font-semibold ${
                          isSelected
                            ? "text-indigo-700 dark:text-indigo-300"
                            : "text-gray-900 dark:text-gray-100"
                        }`}
                      >
                        {language.name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {language.nativeName}
                      </p>
                    </div>

                    {/* Selected Indicator */}
                    {isSelected && (
                      <div className="flex-shrink-0">
                        <div className="w-5 h-5 bg-indigo-600 rounded-full flex items-center justify-center">
                          <svg
                            className="w-3 h-3 text-white"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={3}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        </div>
                      </div>
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Safe area padding for iOS */}
          <div className="h-4" />
        </div>
      </div>
    </>,
    document.body
  );
};
