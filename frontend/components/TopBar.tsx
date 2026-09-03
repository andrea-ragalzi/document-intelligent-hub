"use client";

import { Menu, User } from "lucide-react";
import TierBadge from "./TierBadge";
import type { UserTier } from "@/hooks/useUserTier";

interface TopBarProps {
  onOpenLeftSidebar: () => void;
  onOpenRightSidebar: () => void;
  onNewConversation: () => void;
  hasConversation: boolean;
  tier: UserTier;
  isTierLoading: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  onOpenLeftSidebar,
  onOpenRightSidebar,
  tier,
  isTierLoading,
}) => {
  return (
    <div className="w-full bg-raised border-b border-line/15 transition-colors duration-200 ease-in-out font-[Inter]">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Hamburger Menu - Solo mobile (nascosto su lg+) */}
        <button
          onClick={onOpenLeftSidebar}
          className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-surface-hover transition-all duration-200 ease-in-out text-ink lg:hidden focus:outline-none focus:ring-3 focus:ring-focus"
          aria-label="Toggle navigation"
          title="Conversazioni"
        >
          <Menu size={20} />
        </button>

        {/* Spacer per desktop quando menu è nascosto */}
        <div className="hidden lg:block w-10"></div>

        {/* Center: Title */}
        <div className="flex-1 flex items-center justify-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight text-ink">
            Document Intelligent Hub
          </h1>
          {/* Tier badge - hidden on small screens */}
          {!isTierLoading && (
            <div className="hidden md:block">
              <TierBadge tier={tier} />
            </div>
          )}
        </div>

        {/* Right: User Profile Icon - Solo mobile (nascosto su xl+) */}
        <button
          onClick={onOpenRightSidebar}
          className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-surface-hover transition-all duration-200 ease-in-out text-ink xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
          aria-label="Toggle settings"
          title="Impostazioni"
        >
          <User size={20} />
        </button>

        {/* Spacer per desktop quando menu è nascosto */}
        <div className="hidden xl:block w-10"></div>
      </div>
    </div>
  );
};
