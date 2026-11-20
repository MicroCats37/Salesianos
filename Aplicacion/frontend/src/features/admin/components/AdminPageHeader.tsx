import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface AdminDatoMeta {
  /** The label of the fact. */
  etiqueta: string;
  /** The value of the fact. */
  valor: ReactNode;
}

export interface AdminPageHeaderProps {
  /** The identifier of the route in the plan, e.g. `ADM-05`. */
  pageId: string;
  /** The name of the route, in the words of the operator. */
  title: string;
  /** What this route is for, in one sentence. */
  description: string;
  /** Facts that are known without asking the server. */
  meta?: AdminDatoMeta[];
  /** The primary actions of the route. */
  actions?: ReactNode;
  className?: string;
}

/**
 * AdminPageHeader - the header of an administration route.
 *
 * The eyebrow carries the identifier of the plan, so the operator and the
 * team speak about the same route. The description says what the route is
 * FOR, not what it contains: an operator who lands here must know in one
 * sentence whether this is the place for their task.
 *
 * The header borrows the deep festival stage from the landing and video room:
 * administration opens with a clear sense of place, while the work stays on
 * calm surfaces below it.
 *
 * The actions live on the right and never move: the header is the only
 * stable landmark of the area, and an action that jumps between rows is an
 * action that gets missed.
 */
export function AdminPageHeader({
  pageId,
  title,
  description,
  meta,
  actions,
  className,
}: AdminPageHeaderProps) {
  return (
    <header
      data-route-block
      className={cn(
        "relative isolate flex flex-col gap-5 overflow-hidden rounded-[var(--radius-xl)] border border-brand-deep-blue-mid bg-hero-gradient px-5 py-6 text-brand-on-gradient shadow-[var(--elevation-lg)] sm:px-7 sm:py-7",
        className,
      )}
    >
      <div aria-hidden="true" className="bg-hero-overlay" />
      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between lg:gap-8">
        <div className="flex min-w-0 flex-col gap-2">
          <p className="text-eyebrow-brand text-accent">{pageId}</p>
          <h1 className="text-title-page text-brand-on-gradient">{title}</h1>
          <p className="max-w-measure text-lead text-brand-on-gradient-muted">
            {description}
          </p>
        </div>

        {actions ? (
          <div className="relative flex shrink-0 flex-wrap items-center gap-2">
            {actions}
          </div>
        ) : null}
      </div>

      {meta && meta.length > 0 ? (
        <dl className="relative flex flex-wrap gap-x-8 gap-y-3 border-t border-brand-on-gradient-border pt-4">
          {meta.map((dato) => (
            <div key={dato.etiqueta} className="flex flex-col gap-0.5">
              <dt className="text-eyebrow-brand text-brand-on-gradient-muted">
                {dato.etiqueta}
              </dt>
              <dd className="text-sm font-semibold text-brand-on-gradient">
                {dato.valor}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </header>
  );
}
