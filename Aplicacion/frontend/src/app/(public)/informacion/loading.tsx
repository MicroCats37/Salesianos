import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the information page.
 *
 * It mirrors the real geometry: the band, the index rail and the sections.
 * A spinner over an empty page would not say anything about the shape
 * (SH-03 S-01).
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true">
      <div className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border p-5 sm:p-8">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-80 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)] lg:items-start">
        <div className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <Skeleton className="h-3 w-2/3" />
        </div>

        <div className="flex flex-col gap-10">
          <div className="flex flex-col gap-4">
            <Skeleton className="h-5 w-64" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
          </div>
          <div className="flex flex-col gap-4">
            <Skeleton className="h-5 w-56" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
            <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />
          </div>
        </div>
      </div>
    </div>
  );
}
