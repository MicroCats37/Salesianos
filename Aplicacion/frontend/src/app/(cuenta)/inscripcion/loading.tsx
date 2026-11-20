import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of the wizard of a registration.
 *
 * It mirrors the geometry of the route: the header, the rail of the steps
 * and the panel of the current step.
 */
export default function Loading() {
  return (
    <div className="flex flex-col gap-6" aria-busy="true">
      <div className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border p-5 sm:p-8">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-72 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-4 gap-2">
          <Skeleton className="size-9 rounded-full" />
          <Skeleton className="size-9 rounded-full" />
          <Skeleton className="size-9 rounded-full" />
          <Skeleton className="size-9 rounded-full" />
        </div>
      </div>

      <div className="flex flex-col gap-4 rounded-[var(--radius-xl)] border border-border p-4 sm:p-6">
        <Skeleton className="h-5 w-56" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}
