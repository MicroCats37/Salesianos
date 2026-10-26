"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ADMIN_SECCIONES, adminSeccionActiva } from "../utils/admin.secciones";

/**
 * AdminSeccionNav — the navigation between the seven sections of the area.
 *
 * The active section is DERIVED from the route (`usePathname`), never stored:
 * a hard reload and the browser back button always mark the right section.
 *
 * On a phone the seven labels do NOT fit (≈553px of content in 343px of
 * usable width), so the navigation scrolls INSIDE its own container: the page
 * never scrolls horizontally. The fade on the right is the affordance that
 * says "there is more to the right".
 */
export function AdminSeccionNav() {
  const pathname = usePathname();
  const activa = adminSeccionActiva(pathname);

  return (
    <nav
      aria-label="Secciones de administración"
      className="relative border-b border-slate-200"
    >
      <ul className="flex items-stretch gap-1 overflow-x-auto px-4 sm:px-6 lg:px-10">
        {ADMIN_SECCIONES.map((seccion) => {
          const esActiva = activa?.id === seccion.id;

          return (
            <li key={seccion.id} className="shrink-0">
              <Link
                href={seccion.href}
                aria-current={esActiva ? "page" : undefined}
                className={cn(
                  "flex min-h-11 items-center gap-2 whitespace-nowrap border-b-2 px-3 text-xs font-black uppercase tracking-wider transition-colors focus-visible:ring-2 focus-visible:ring-[#312e8e]/40 focus-visible:ring-offset-2 focus-visible:outline-none",
                  esActiva
                    ? "border-[#312e8e] text-[#312e8e]"
                    : "border-transparent text-slate-500 hover:text-slate-800",
                )}
              >
                <seccion.icon className="size-4 shrink-0" aria-hidden="true" />
                {seccion.title}
              </Link>
            </li>
          );
        })}
      </ul>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-background to-transparent"
      />
    </nav>
  );
}
