/**
 * Skeleton loader for document list
 * Shows placeholder cards while documents are loading
 */
interface DocumentListSkeletonProps {
  count?: number;
}

export const DocumentListSkeleton: React.FC<DocumentListSkeletonProps> = ({ count = 3 }) => {
  return (
    <div className="space-y-2 max-h-72 overflow-y-hidden">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3 animate-pulse"
        >
          <div className="flex items-start gap-3">
            {/* Icon skeleton */}
            <div className="flex-shrink-0 w-9 h-9 bg-gray-300 dark:bg-gray-700 rounded-lg"></div>

            {/* Content skeleton */}
            <div className="flex-1 space-y-2">
              {/* Filename skeleton */}
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>

              {/* Metadata skeleton */}
              <div className="flex items-center gap-2">
                <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded-full w-20"></div>
                <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded-full w-12"></div>
              </div>
            </div>

            {/* Delete button skeleton */}
            <div className="flex-shrink-0 w-8 h-8 bg-gray-200 dark:bg-gray-800 rounded-lg"></div>
          </div>
        </div>
      ))}
    </div>
  );
};
