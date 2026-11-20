"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export interface AdminSubnavItem {
  /** The route of the section. */
  href: string;
  /** The name of the section. */
  label: string;
  /** What the section answers, in a few words. */
  description?: string;
}

export interface AdminSubnavProps {
  /** The accessible name of the navigation. */
  ariaLabel: string;
  /** The sections of the route. */
  items: AdminSubnavItem[];
  className?: string;
}

/**
 * AdminSubnav - the secondary navigation of a route.
 *
 * Some sections of the area are split in pages of their own (competencias:
 * lista, agenda y cuadro; tienda: productos, pedidos, inventario y
 * recogidas). This navigation says, in the route itself, which of them the
 * operator is looking at, and it is a list of LINKS: the section lives in
 * the URL, it survives a reload and it can be shared.
 *
 * The active section is derived from the route on every render, never
 * stored: a hard reload and the browser back button always mark the right
 * section.
 */
export function AdminSubnav({
  ariaLabel,
  items,
  className,
}: AdminSubnavProps) {
  const pathname = usePathname();

  /**
   * The active section is the MOST SPECIFIC one that matches: `/agenda` is a
   * child of `/competencias`, and only one of them may be marked.
   */
  const activoHref = items
    .filter(
      (item) =>
        pathname === item.href || pathname.startsWith(`${item.href}/`),
    )
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;

  return (
    <nav aria-label={ariaLabel} className={cn("min-w-0", className)}>
      <ul className="-mx-1 flex snap-x gap-2 overflow-x-auto px-1 pb-1">
        {items.map((item) => {
          const activo = item.href === activoHref;

          return (
            <li key={item.href} className="snap-start">
              <Link
                href={item.href}
                aria-current={activo ? "page" : undefined}
                className={cn(
                  "flex min-h-11 flex-col justify-center gap-0.5 rounded-[var(--radius-md)] border px-3 py-2 transition-colors duration-(--motion-duration-fast)",
                  activo
                    ? "border-accent bg-muted font-semibold text-foreground"
                    : "border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <span className="whitespace-nowrap text-sm">{item.label}</span>
                {item.description ? (
                  <span className="whitespace-nowrap text-xs font-normal">
                    {item.description}
                  </span>
                ) : null}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
