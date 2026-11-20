import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the registrations list.
 *
 * It mirrors a LIST: the filter bar and the rows, not the grid of cards the
 * group skeleton draws (SH-03 S-01).
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-6" aria-busy="true">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-64 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4">
        <Skeleton className="h-4 w-24" />
        <div className="grid gap-3 sm:grid-cols-2">
          <Skeleton className="h-11 w-full" />
          <Skeleton className="h-11 w-full" />
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, indice) => (
          <div
            key={indice}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4"
          >
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-72 max-w-full" />
            <Skeleton className="h-10 w-44" />
          </div>
        ))}
      </div>
    </div>
  );
}
