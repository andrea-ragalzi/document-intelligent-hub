import {
  Sparkles,
  Code,
  BarChart,
  Lightbulb,
  Calendar,
  TrendingUp,
  Wand2,
} from "lucide-react";
import { createPortal } from "react-dom";
import { useState, useRef } from "react";

export interface UseCase {
  id: string;
  name: string;
  icon: React.ReactNode;
}

export const USE_CASES: UseCase[] = [
  {
    id: "AUTO",
    name: "Generic",
    icon: <Wand2 size={20} />,
  },
  {
    id: "CU1",
    name: "Report Analysis",
    icon: <Sparkles size={20} />,
  },
  {
    id: "CU2",
    name: "Code Generation",
    icon: <Code size={20} />,
  },
  {
    id: "CU3",
    name: "Complex Analysis",
    icon: <BarChart size={20} />,
  },
  {
    id: "CU4",
    name: "Creative Brainstorming",
    icon: <Lightbulb size={20} />,
  },
  {
    id: "CU5",
    name: "Project Planning",
    icon: <Calendar size={20} />,
  },
  {
    id: "CU6",
    name: "Business Strategy",
    icon: <TrendingUp size={20} />,
  },
];

interface UseCaseSelectorProps {
  isOpen: boolean;
  selectedUseCaseId: string;
  onSelectUseCase: (id: string) => void;
  onClose: () => void;
}

export const UseCaseSelector: React.FC<UseCaseSelectorProps> = ({
  isOpen,
  selectedUseCaseId,
  onSelectUseCase,
  onClose,
}) => {
  const [dragY, setDragY] = useState(0);
  const dragStartY = useRef(0);

  if (!isOpen) return null;

  const handleCardClick = (id: string) => {
    onSelectUseCase(id);
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
      {/* Backdrop - same style as conversations/documents */}
      <div
        role="presentation"
        className="fixed inset-0 bg-black/90 dark:bg-indigo-950/95 z-[100]"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
      />

      {/* Mobile Bottom Sheet - with top padding to avoid topbar */}
      <div className="fixed inset-0 z-[110] flex items-end justify-center pt-20">
        <div
          className="bg-white dark:bg-gray-800 rounded-t-3xl shadow-2xl w-full overflow-hidden flex flex-col transition-transform"
          style={{
            maxHeight: "calc(100vh - 5rem)",
            transform: `translateY(${dragY}px)`,
          }}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
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

          {/* Use Cases List - starting from bottom */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {USE_CASES.map((useCase) => {
              const isSelected = selectedUseCaseId === useCase.id;

              return (
                <button
                  key={useCase.id}
                  onClick={() => handleCardClick(useCase.id)}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                    isSelected
                      ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-500"
                      : "bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600 hover:bg-indigo-50/50 dark:hover:bg-gray-600"
                  }`}
                >
                  {/* Icon next to title */}
                  <div
                    className={`flex-shrink-0 ${
                      isSelected
                        ? "text-indigo-600 dark:text-indigo-400"
                        : "text-gray-600 dark:text-gray-400"
                    }`}
                  >
                    {useCase.icon}
                  </div>

                  {/* Title */}
                  <h3
                    className={`flex-1 text-base font-semibold ${
                      isSelected
                        ? "text-indigo-700 dark:text-indigo-300"
                        : "text-gray-900 dark:text-gray-100"
                    }`}
                  >
                    {useCase.name}
                  </h3>

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
            })}
          </div>

          {/* Safe area padding for iOS */}
          <div className="h-4" />
        </div>
      </div>
    </>,
    document.body
  );
};
