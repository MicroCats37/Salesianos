"use client";

import { SearchX } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";

export interface SinResultadosConFiltrosProps {
  /** The keys of the filters that are active in the URL. */
  claves: string[];
  /** How many records exist BEFORE the filters were applied. */
  totalSinFiltrar: number;
  className?: string;
}

/**
 * SinResultadosConFiltros - the filtered-empty state (SH-03 S-03).
 *
 * Data exists but the active filters exclude it. The message says so
 * instead of pretending the account is empty, it states how many records are
 * being filtered out, and it offers the way back: the filters stay visible
 * and the action that clears them is one click away.
 *
 * The filters are never removed silently: the reader has to know that the
 * list is empty BECAUSE of what they chose.
 */
export function SinResultadosConFiltros({
  claves,
  totalSinFiltrar,
  className,
}: SinResultadosConFiltrosProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activos = claves.filter((clave) => searchParams.get(clave));

  function limpiar() {
    const params = new URLSearchParams(searchParams.toString());
    for (const clave of claves) {
      params.delete(clave);
    }
    const consulta = params.toString();
    router.replace(consulta ? `${pathname}?${consulta}` : (pathname ?? "/"));
  }

  return (
    <Empty className={className}>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <SearchX className="size-5" aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle className="text-base">
          Ninguno de tus registros coincide con los filtros
        </EmptyTitle>
        <EmptyDescription>
          {activos.length === 1
            ? "Hay 1 filtro activo y está ocultando "
            : `Hay ${activos.length} filtros activos y están ocultando `}
          {totalSinFiltrar === 1
            ? "1 registro."
            : `${totalSinFiltrar} registros.`}{" "}
          Tus registros siguen aquí: cambia el filtro o quítalo.
        </EmptyDescription>
      </EmptyHeader>
      <Button variant="outline" onClick={limpiar} className="min-h-11">
        Quitar los filtros
      </Button>
    </Empty>
  );
}
