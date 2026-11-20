"use client";

import { Filter, SlidersHorizontal } from "lucide-react";
import { useId } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import type { FiltroOperativo } from "../types/operaciones.types";

/** The value that means "no filter". */
const SIN_FILTRO = "__todos__";

export interface BarraFiltrosProps {
  /** The filters of the list. */
  filtros: FiltroOperativo[];
  /**
   * EVERY query parameter of the current URL.
   *
   * The filters live in the URL and nowhere else (`GOV-02-RB-03b`), so the
   * view is shareable and survives a reload.
   */
  parametros: Record<string, string>;
  /** The name of the filter region, in the words of the operator. */
  etiqueta: string;
  className?: string;
}

/**
 * BarraFiltros - the filter bar of an operational list.
 *
 * `D-UI01-10`: the bar is a client component that WRITES THE URL, and the
 * page reads the query string. The filtering is therefore a query and never
 * a business rule of the browser.
 *
 * At 360 and 390 the filters live in a SHEET, because a row of selects does
 * not fit a phone. From 768 they are inline. The two compositions are the
 * same filters and the same URLs.
 */
export function BarraFiltros({
  filtros,
  parametros,
  etiqueta,
  className,
}: BarraFiltrosProps) {
  const router = useRouter();
  const pathname = usePathname();
  const idBase = useId();

  const activos = filtros.filter(
    (filtro) => (parametros[filtro.clave] ?? "") !== "",
  );

  function escribir(cambios: Record<string, string | null>) {
    const siguiente: Record<string, string> = { ...parametros };

    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor === null || valor === "") {
        delete siguiente[clave];
      } else {
        siguiente[clave] = valor;
      }
    }

    const query = new URLSearchParams(siguiente).toString();
    router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  function limpiar() {
    const siguiente: Record<string, string> = { ...parametros };

    for (const filtro of filtros) {
      delete siguiente[filtro.clave];
    }

    const query = new URLSearchParams(siguiente).toString();
    router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  const controles = filtros.map((filtro) => {
    const idEtiqueta = `${idBase}-${filtro.clave}-etiqueta`;
    const valor = parametros[filtro.clave] ?? "";
    const deshabilitado = filtro.opciones.length === 0 && filtro.tipo !== "fecha";

    if (filtro.tipo === "fecha") {
      return (
        <div key={filtro.clave} className="flex flex-col gap-1.5">
          <label
            htmlFor={`${idBase}-${filtro.clave}-control`}
            className="text-xs font-semibold tracking-[0.04em] text-foreground-muted uppercase"
          >
            {filtro.etiqueta}
          </label>
          <Input
            id={`${idBase}-${filtro.clave}-control`}
            type="date"
            value={valor}
            className="min-h-11 bg-surface-raised text-sm"
            onChange={(evento) =>
              escribir({ [filtro.clave]: evento.target.value || null })
            }
          />
        </div>
      );
    }

    return (
      <div key={filtro.clave} className="flex flex-col gap-1.5">
        <span
          id={idEtiqueta}
          className="text-xs font-semibold tracking-[0.04em] text-foreground-muted uppercase"
        >
          {filtro.etiqueta}
        </span>
        <Select
          value={valor || SIN_FILTRO}
          disabled={deshabilitado}
          onValueChange={(siguiente) =>
            escribir({
              [filtro.clave]: siguiente === SIN_FILTRO ? null : siguiente,
            })
          }
        >
          <SelectTrigger
            id={`${idBase}-${filtro.clave}-control`}
            aria-labelledby={idEtiqueta}
            className="min-h-11 w-full bg-surface-raised text-sm"
          >
            <SelectValue placeholder="Todos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={SIN_FILTRO}>Todos</SelectItem>
            {filtro.opciones.map((opcion) => (
              <SelectItem key={opcion.valor} value={opcion.valor}>
                {opcion.etiqueta}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {deshabilitado && filtro.sinOpciones ? (
          <p className="text-xs leading-snug text-foreground-muted">
            {filtro.sinOpciones}
          </p>
        ) : null}
      </div>
    );
  });

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {/* 360 · 390 — the filters travel in a sheet. */}
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" className="min-h-11 justify-between md:hidden">
            <span className="inline-flex items-center gap-2">
              <SlidersHorizontal className="size-4" aria-hidden="true" />
              {etiqueta}
            </span>
            {activos.length > 0 ? (
              <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground">
                {activos.length}
              </span>
            ) : null}
          </Button>
        </SheetTrigger>
        <SheetContent
          side="bottom"
          showCloseButton={false}
          className="max-h-[85vh] overflow-y-auto"
        >
          <SheetHeader>
            <SheetTitle>{etiqueta}</SheetTitle>
            <SheetDescription>
              Los filtros se guardan en la dirección de la página: la vista se
              puede compartir y sigue funcionando al recargarla.
            </SheetDescription>
          </SheetHeader>
          <div className="flex flex-col gap-4 px-4">{controles}</div>
          <SheetFooter className="flex-row justify-end gap-2">
            {activos.length > 0 ? (
              <Button variant="outline" onClick={limpiar}>
                Limpiar filtros
              </Button>
            ) : null}
            <SheetClose asChild>
              <Button>Cerrar</Button>
            </SheetClose>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* 768 and above — the same filters, inline. */}
      <div className="hidden md:flex md:flex-wrap md:items-end md:gap-3">
        {controles}
        {activos.length > 0 ? (
          <Button variant="ghost" onClick={limpiar} className="min-h-11">
            <Filter className="size-4" aria-hidden="true" />
            Limpiar filtros
          </Button>
        ) : null}
      </div>
    </div>
  );
}
