"use client";

import { Skeleton } from "@/components/ui/skeleton";

/**
 * The loading skeleton of this group.
 *
 * It mirrors the real shape of the content, so the layout does not jump when
 * the data arrives. A spinner would not say anything about the shape.
 */
export default function Loading() {
  return (
    <div
      className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-10"
      aria-busy="true"
    >
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-72 max-w-full" />
        <Skeleton className="h-4 w-96 max-w-full" />
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-[--radius-lg] border border-border p-5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-3 w-full" />
        </div>
      </div>
    </div>
  );
}
