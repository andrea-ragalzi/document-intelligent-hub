import type { ReactNode } from "react";

interface AuthVisibilityProps {
  isGuest: boolean;
  children: ReactNode;
}

export function GuestOnly({ isGuest, children }: AuthVisibilityProps) {
  return isGuest ? children : null;
}

export function RegisteredOnly({ isGuest, children }: AuthVisibilityProps) {
  return isGuest ? null : children;
}
