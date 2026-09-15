export function LoadingSpinner({ size = "md", text }: { size?: "sm" | "md" | "lg"; text?: string }) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3 p-8">
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-stone-200 border-t-emerald-700`}
      />
      {text && <p className="text-sm text-stone-500">{text}</p>}
    </div>
  );
}

export function VerseSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-full bg-stone-200" />
          <div className="h-4 w-24 rounded bg-stone-200" />
        </div>
        <div className="h-6 w-20 rounded-full bg-stone-200" />
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-6 w-3/4 rounded bg-stone-200" />
        <div className="h-6 w-1/2 rounded bg-stone-200" />
      </div>
      <div className="mt-3 space-y-2">
        <div className="h-4 w-full rounded bg-stone-200" />
        <div className="h-4 w-2/3 rounded bg-stone-200" />
      </div>
    </div>
  );
}

export function ChapterSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-stone-200 bg-white p-5 text-center shadow-sm">
      <div className="mx-auto h-8 w-48 rounded bg-stone-200" />
      <div className="mx-auto mt-2 h-10 w-32 rounded bg-stone-200" />
      <div className="mx-auto mt-2 h-4 w-40 rounded bg-stone-200" />
    </div>
  );
}
