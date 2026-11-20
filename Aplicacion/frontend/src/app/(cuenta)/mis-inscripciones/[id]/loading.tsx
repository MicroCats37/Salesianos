import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the detail of a registration.
 *
 * It mirrors the header, the tabs and the band of the cupos.
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

      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-2">
          <Skeleton className="h-11 w-24" />
          <Skeleton className="h-11 w-24" />
          <Skeleton className="h-11 w-28" />
          <Skeleton className="h-11 w-24" />
          <Skeleton className="h-11 w-28" />
        </div>

        <div className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-4 sm:flex-row sm:justify-between">
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-10 w-20" />
            <Skeleton className="h-10 w-20" />
            <Skeleton className="h-10 w-20" />
          </div>
          <Skeleton className="h-10 w-72 max-w-full" />
        </div>
      </div>
    </div>
  );
}
