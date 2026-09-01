interface ChatLoadingSkeletonProps {
  isQuerying: boolean;
}

export const ChatLoadingSkeleton: React.FC<ChatLoadingSkeletonProps> = ({ isQuerying }) => {
  if (!isQuerying) return null;

  return (
    <div className="flex justify-start mb-6 px-1 sm:px-2">
      <div className="flex-shrink-0 mr-2 w-8 h-8"></div>
      <div className="max-w-[85%] sm:max-w-[80%] flex flex-col">
        <div className="text-xs font-medium mb-1 text-muted pl-2">Assistant</div>
        <div className="p-3 sm:p-4 rounded-xl shadow-sm bg-surface rounded-tl-sm border border-line/15">
          {/* Skeleton Loader - Animate Pulse with Gradient */}
          <div className="mt-1 space-y-2 animate-pulse">
            <div className="h-3 bg-accent/25 rounded-lg w-3/4"></div>
            <div className="h-3 bg-raised rounded-lg w-full"></div>
            <div className="h-3 bg-raised rounded-lg w-5/6"></div>
          </div>
        </div>
      </div>
    </div>
  );
};
