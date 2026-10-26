"use client";

import { ArrowUpRight, GitBranch, Swords } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

/** The three surfaces of the module. */
const SECCIONES = [
  {
    id: "lista",
    href: "/administracion/competencias",
    etiqueta: "Competencias",
  },
  {
    id: "cuadro",
    href: "/administracion/competencias/cuadro",
    etiqueta: "Cuadro",
  },
  {
    id: "agenda",
    href: "/administracion/competencias/agenda",
    etiqueta: "Agenda",
  },
];

/**
 * CompetenciasSubnav — the navigation between the three surfaces of the
 * module.
 *
 * The active surface is DERIVED from the route (`usePathname`), never stored:
 * a hard reload and the browser back button always mark the right one.
 */
export function CompetenciasSubnav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Secciones de competencias"
      className="border-b border-slate-200"
    >
      <ul className="flex items-stretch gap-1 overflow-x-auto px-4 sm:px-6 lg:px-10">
        {SECCIONES.map((seccion) => {
          const esActiva =
            pathname === seccion.href ||
            pathname.startsWith(`${seccion.href}/`);

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
                {seccion.id === "lista" ? (
                  <Swords className="size-4 shrink-0" aria-hidden="true" />
                ) : null}
                {seccion.id === "cuadro" ? (
                  <GitBranch className="size-4 shrink-0" aria-hidden="true" />
                ) : null}
                {seccion.etiqueta}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * CompetenciasEnlaceCuadro — the link from a row to the bracket of its
 * competition.
 *
 * The bracket lives in a SIBLING route and owns its competition in the URL
 * (`?id=`), so the link is shareable.
 */
export function CompetenciasEnlaceCuadro({
  competenciaId,
  className,
}: {
  competenciaId: string;
  className?: string;
}) {
  return (
    <Link
      href={`/administracion/competencias/cuadro?id=${competenciaId}`}
      className={cn(
        "inline-flex items-center gap-1 text-[11px] font-black uppercase tracking-wider text-[#312e8e] hover:underline",
        className,
      )}
    >
      <ArrowUpRight className="size-3" aria-hidden="true" />
      Cuadro
    </Link>
  );
}
