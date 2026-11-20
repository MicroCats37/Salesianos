import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the recovery page.
 *
 * It mirrors the card with the two fields, so the form does not jump when
 * it arrives.
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true">
      <div className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border p-5 sm:p-8">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-72 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="mx-auto flex w-full max-w-[480px] flex-col gap-4 rounded-[var(--radius-lg)] border border-border p-5 sm:p-6">
        <Skeleton className="h-5 w-56" />
        <Skeleton className="h-4 w-full" />
        <div className="flex flex-col gap-1.5">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-11 w-full" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-11 w-full" />
        </div>
        <Skeleton className="h-11 w-full" />
      </div>
    </div>
  );
}
