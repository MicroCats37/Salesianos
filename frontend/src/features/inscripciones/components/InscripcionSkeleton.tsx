"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-2xl bg-slate-200/70", className)}
    />
  );
}

/**
 * Loading skeleton of the inscription detail.
 *
 * It mirrors the real layout (hero + two columns) so the page does not jump
 * when the data arrives.
 */
export function InscripcionSkeleton() {
  return (
    <div className="surface-page-gradient min-h-svh w-full">
      <div className="border-b border-slate-200/60 bg-gradient-to-br from-[#f6f4ee] via-white to-[#eef1f8]">
        <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
          <div className="flex flex-col gap-5">
            <Skeleton className="h-12 w-56 rounded-full" />
            <Skeleton className="h-9 w-72" />
            <Skeleton className="h-4 w-52" />
          </div>
          <div className="rounded-3xl border border-slate-200/70 bg-white/85 p-5">
            <div className="flex items-center gap-3">
              <Skeleton className="size-11 rounded-2xl" />
              <div className="space-y-2">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-5 w-48" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
        <div className="flex flex-col gap-6 xl:grid xl:grid-cols-12 xl:gap-8">
          <div className="order-1 space-y-8 xl:col-span-8">
            <Skeleton className="h-80 rounded-3xl" />
            <Skeleton className="h-48 rounded-3xl" />
            <Skeleton className="h-64 rounded-3xl" />
          </div>
          <div className="order-2 space-y-4 xl:col-span-4">
            <Skeleton className="h-56 rounded-3xl" />
            <Skeleton className="h-40 rounded-3xl" />
          </div>
        </div>
      </div>

      <output className="sr-only">Cargando detalle de la inscripcion...</output>
    </div>
  );
}
