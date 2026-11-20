import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the administration area.
 *
 * It mirrors the REAL shape of the area: the header of the route and then
 * the blocks of the console. A grid of six identical tiles would promise a
 * dashboard that the route does not have, and the layout would jump when
 * the content arrived.
 */
export default function Loading() {
  return (
    <div
      className="mx-auto flex w-full max-w-page flex-col gap-6"
      aria-busy="true"
    >
      <div className="flex flex-col gap-3 border-b border-border pb-6">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-9 w-72 max-w-full" />
        <Skeleton className="h-5 w-full max-w-2xl" />
      </div>

      <div className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-card p-4">
        <Skeleton className="h-5 w-56" />
        <Skeleton className="h-4 w-full max-w-xl" />
        <div className="flex flex-col gap-2 pt-2">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-3/4" />
        </div>
      </div>
    </div>
  );
}
