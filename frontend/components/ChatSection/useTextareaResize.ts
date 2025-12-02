/**
 * Custom hook for textarea auto-resize functionality
 */

import { useRef, FormEvent, ChangeEvent } from "react";

const INITIAL_HEIGHT = 44;
const MAX_HEIGHT = 144; // ~6 lines

export function useTextareaResize() {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = `${INITIAL_HEIGHT}px`;
    }
  };

  const handleInput = (e: FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement;

    // Reset height to get proper scrollHeight
    target.style.height = `${INITIAL_HEIGHT}px`;

    // Calculate new height with max constraint
    const newHeight = Math.min(target.scrollHeight, MAX_HEIGHT);
    target.style.height = `${newHeight}px`;
  };

  const handleChange = (
    e: ChangeEvent<HTMLTextAreaElement>,
    onQueryChange: (value: string) => void
  ) => {
    onQueryChange(e.target.value);
    handleInput(e);
  };

  return {
    textareaRef,
    resetHeight,
    handleInput,
    handleChange,
  };
}
