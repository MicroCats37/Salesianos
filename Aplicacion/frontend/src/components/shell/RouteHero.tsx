import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface RouteHeroDato {
  /** The label of the fact. */
  label: string;
  /** The value of the fact. */
  value: ReactNode;
}

export interface RouteHeroProps {
  /** The identifier of the route in the plan, e.g. `ACCOUNT-01`. */
  pageId: string;
  /** The name of the route, in the words of the person who reads it. */
  title: string;
  /** What this route is for, in one sentence. */
  description: string;
  /** The primary action of the route. */
  actions?: ReactNode;
  /** Facts that are known without asking the server. */
  facts?: RouteHeroDato[];
  /**
   * The tone of the header.
   *
   * `band` is the institutional band: a soft gradient of cyan to gold that
   * breathes very slowly. It is the default because it is WELCOME, and the
   * product greets the visitor with light and colour.
   *
   * `hero` is the dark gradient of the brand: it is reserved for the
   * moments that ARE the identity (the portada, the access). `surface` is
   * the sober one for the blocks inside a page.
   */
  tone?: "surface" | "band" | "hero";
  className?: string;
}

/**
 * RouteHero - the header of a page of the public and account families.
 *
 * The band carries the brand gradient as a SOFT, slow, welcoming surface:
 * a band of cyan that fades into gold through the surface of the page. The
 * gradient is an accent, never the wallpaper: it is the header and nothing
 * else.
 *
 * The gradient never carries the meaning by itself: the eyebrow, the title
 * and the sentence below it are the hierarchy. The gradient only says
 * "this is a moment", not "this is important".
 */
export function RouteHero({
  pageId,
  title,
  description,
  actions,
  facts,
  tone = "band",
  className,
}: RouteHeroProps) {
  const esHero = tone === "hero";
  const esBanda = tone === "band";

  return (
    <header
      data-route-block
      className={cn(
        "relative overflow-hidden rounded-[var(--radius-xl)] border",
        esHero
          ? "border-brand-deep-blue-mid bg-hero-gradient text-brand-on-gradient shadow-[var(--elevation-lg)]"
          : esBanda
            ? "border-border bg-brand-band text-foreground shadow-[var(--elevation-md)]"
            : "border-border bg-surface-elevated text-card-foreground shadow-[var(--elevation-sm)]",
        className,
      )}
    >
      {esHero ? <div aria-hidden="true" className="bg-hero-overlay" /> : null}

      <div className="relative flex flex-col gap-5 px-5 py-7 sm:px-8 sm:py-9">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between lg:gap-10">
          <div className="flex min-w-0 flex-col gap-2">
            <p
              className={cn(
                "text-eyebrow-brand",
                esHero ? "text-accent" : "text-primary",
              )}
            >
              {pageId}
            </p>
            <h1
              className={cn(
                "text-title-page",
                esHero ? "text-brand-on-gradient" : "text-foreground",
              )}
            >
              {title}
            </h1>
            <p
              className={cn(
                "max-w-measure text-lead",
                esHero
                  ? "text-brand-on-gradient-muted"
                  : "text-muted-foreground",
              )}
            >
              {description}
            </p>
          </div>

          {actions ? (
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              {actions}
            </div>
          ) : null}
        </div>

        {facts && facts.length > 0 ? (
          <dl
            className={cn(
              "flex flex-wrap gap-x-8 gap-y-3 border-t pt-5",
              esHero ? "border-brand-on-gradient-border" : "border-border/70",
            )}
          >
            {facts.map((dato) => (
              <div key={dato.label} className="flex flex-col gap-0.5">
                <dt
                  className={cn(
                    "text-eyebrow-brand",
                    esHero
                      ? "text-brand-on-gradient-muted"
                      : "text-muted-foreground",
                  )}
                >
                  {dato.label}
                </dt>
                <dd
                  className={cn(
                    "text-sm font-semibold",
                    esHero ? "text-brand-on-gradient" : "text-foreground",
                  )}
                >
                  {dato.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}
      </div>
    </header>
  );
}
