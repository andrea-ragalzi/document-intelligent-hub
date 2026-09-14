import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import TierLimitsDisplay from "@/components/TierLimitsDisplay";
import { ChatEmptyState } from "@/components/ChatSection/ChatEmptyState";
import { getPlaceholderText } from "@/components/ChatSection/placeholderText";

const freeTierProps = {
  tier: "FREE" as const,
  limits: {
    maxDocuments: 5,
    maxQueriesPerDay: 20,
    canUploadMultiple: false,
    hasAdvancedFeatures: false,
  },
  isLoading: false,
};

describe("public FREE-only UI", () => {
  it("does not show FREE counters while the authenticated tier is loading", () => {
    render(
      <TierLimitsDisplay
        currentDocuments={5}
        currentQueries={20}
        {...freeTierProps}
        isLoading={true}
      />
    );

    expect(screen.getByText("Your Plan")).toBeInTheDocument();
    expect(screen.queryByText("5 / 5")).not.toBeInTheDocument();
    expect(screen.getByText("Loading plan…")).toBeInTheDocument();
  });

  it("does not advertise an upgrade when a FREE user nears a limit", () => {
    render(<TierLimitsDisplay currentDocuments={5} currentQueries={20} {...freeTierProps} />);

    expect(screen.getByText("Your Plan")).toBeInTheDocument();
    expect(screen.queryByText(/Upgrade for more capacity/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Pro/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Unlimited/i)).not.toBeInTheDocument();
  });

  it("keeps the limit message informative without suggesting an upgrade", () => {
    render(
      <ChatEmptyState
        isCheckingDocuments={false}
        isServerOnline
        isLimitReached
        noDocuments={false}
        demoDocumentState="idle"
        suggestedQuestions={[]}
        onSelectQuestion={vi.fn()}
        onOpenUpload={vi.fn()}
      />
    );

    expect(screen.getByText(/try again tomorrow/i)).toBeInTheDocument();
    expect(screen.queryByText(/Upgrade/i)).not.toBeInTheDocument();
    expect(getPlaceholderText(true, true, false)).not.toMatch(/Upgrade/i);
  });
});
