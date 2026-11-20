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
 * The band carries the GRADIENT of the brand: the console of the event is
 * the blue of Salesianos, and every route opens on the same institutional
 * surface. The gradient is the identity of the area, not a decoration that
 * repeats itself on every card.
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
        "relative flex flex-col gap-5 overflow-hidden rounded-[var(--radius-xl)] border border-border bg-brand-band px-5 py-6 text-foreground shadow-[var(--elevation-md)] sm:px-7 sm:py-7",
        className,
      )}
    >
      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between lg:gap-8">
        <div className="flex min-w-0 flex-col gap-2">
          <p className="text-eyebrow-brand text-primary">{pageId}</p>
          <h1 className="text-title-page text-foreground">{title}</h1>
          <p className="max-w-measure text-lead text-muted-foreground">
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
        <dl className="relative flex flex-wrap gap-x-8 gap-y-3 border-t border-border/70 pt-4">
          {meta.map((dato) => (
            <div key={dato.etiqueta} className="flex flex-col gap-0.5">
              <dt className="text-eyebrow-brand text-muted-foreground">
                {dato.etiqueta}
              </dt>
              <dd className="text-sm font-semibold text-foreground">
                {dato.valor}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </header>
  );
}
