import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface AdminPageHeaderProps {
  eyebrow: string;
  title: string;
  description?: string;
  icon?: LucideIcon;
  badges?: ReactNode;
  actions?: ReactNode;
  size?: "hero" | "compact";
  className?: string;
}

export function AdminPageHeader({
  eyebrow,
  title,
  description,
  icon: Icon,
  badges,
  actions,
  size = "compact",
  className,
}: AdminPageHeaderProps) {
  const esHero = size === "hero";

  return (
    <header
      className={cn(
        "relative w-full overflow-hidden",
        esHero &&
          "border-b border-slate-200/60 bg-gradient-to-br from-[#f6f4ee] via-white to-[#eef1f8]",
        className,
      )}
    >
      {esHero ? (
        <>
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-amber-300/40 blur-3xl" />
          <div className="pointer-events-none absolute -left-24 bottom-0 h-72 w-72 rounded-full bg-cyan-300/40 blur-3xl" />
        </>
      ) : null}

      <div
        className={cn(
          "relative mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-10",
          esHero ? "py-8 sm:py-10" : "py-6 sm:py-8",
        )}
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 space-y-3">
            {esHero ? (
              <>
                <p className="text-eyebrow-brand">{eyebrow}</p>
                <h1 className="text-2xl font-black tracking-tight text-[#17214b] sm:text-4xl">
                  {title}
                </h1>
              </>
            ) : (
              <div className="flex items-center gap-3">
                {Icon ? (
                  <span className="flex size-11 items-center justify-center rounded-2xl border border-[#312e8e]/20 bg-[#312e8e]/10 text-[#312e8e]">
                    <Icon className="size-5" />
                  </span>
                ) : null}
                <div className="space-y-1">
                  <p className="text-eyebrow-brand">{eyebrow}</p>
                  <h1 className="text-xl font-black tracking-tight text-[#17214b] sm:text-2xl">
                    {title}
                  </h1>
                </div>
              </div>
            )}

            {description ? (
              <p className="max-w-3xl text-sm leading-relaxed text-slate-600">
                {description}
              </p>
            ) : null}

            {badges ? (
              <div className="flex flex-wrap items-center gap-2">{badges}</div>
            ) : null}
          </div>

          {actions ? (
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              {actions}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
