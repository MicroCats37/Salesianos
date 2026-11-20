import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the detail of a purchase.
 *
 * It mirrors the summary card and the two blocks that follow it.
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-6" aria-busy="true">
      <div className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border p-5 sm:p-8">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-56 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
        <Skeleton className="h-11 w-44" />
      </div>

      <div className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border p-5">
        <Skeleton className="h-5 w-40" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>

      <div className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border p-5">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
    </div>
  );
}
