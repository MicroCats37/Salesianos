import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the purchases list.
 *
 * It mirrors a LIST: the filter bar and the rows.
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-6" aria-busy="true">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-56 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-11 w-full sm:w-64" />
      </div>

      <div className="flex flex-col gap-3">
        {Array.from({ length: 3 }).map((_, indice) => (
          <div
            key={indice}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4"
          >
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-64 max-w-full" />
            <Skeleton className="h-10 w-36" />
          </div>
        ))}
      </div>
    </div>
  );
}
