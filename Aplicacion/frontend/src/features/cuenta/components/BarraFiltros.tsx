"use client";

import { ListFilter, RotateCcw } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

/** One option of a filter. */
export interface OpcionFiltro {
  valor: string;
  etiqueta: string;
}

/** One filter of a bar. */
export interface DefinicionFiltro {
  /** The key of the filter in the URL. */
  clave: string;
  /** The label of the control. */
  etiqueta: string;
  /** The options the control offers. */
  opciones: OpcionFiltro[];
  /** The value that means "no filter". */
  valorTodos?: string;
}

export interface BarraFiltrosProps {
  definiciones: DefinicionFiltro[];
  className?: string;
}

/**
 * BarraFiltros - the filters of a list, and they live in the URL.
 *
 * The filters of the account are the ones of the administration: the state
 * of the list is a URL, so a filtered list can be shared, bookmarked and
 * restored with the back button (`RB-01` ACCOUNT-02 acceptance).
 *
 * The component NEVER filters anything: it writes the URL and the server
 * reads it back. A filter is not a business rule, it is a query.
 */
export function BarraFiltros({ definiciones, className }: BarraFiltrosProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activos = definiciones.filter((definicion) => {
    const valor = searchParams.get(definicion.clave);
    return Boolean(valor) && valor !== (definicion.valorTodos ?? "");
  });

  function escribir(clave: string, valor: string) {
    const params = new URLSearchParams(searchParams.toString());

    if (
      !valor ||
      valor === (definiciones.find((d) => d.clave === clave)?.valorTodos ?? "")
    ) {
      params.delete(clave);
    } else {
      params.set(clave, valor);
    }

    const consulta = params.toString();
    router.replace(consulta ? `${pathname}?${consulta}` : (pathname ?? "/"));
  }

  function limpiar() {
    const params = new URLSearchParams(searchParams.toString());
    for (const definicion of definiciones) {
      params.delete(definicion.clave);
    }
    const consulta = params.toString();
    router.replace(consulta ? `${pathname}?${consulta}` : (pathname ?? "/"));
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4",
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-caption font-semibold text-foreground">
          <ListFilter className="size-4 text-primary" aria-hidden="true" />
          Filtros
        </p>
        {activos.length > 0 ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={limpiar}
            className="min-h-11"
          >
            <RotateCcw className="size-4" aria-hidden="true" />
            Quitar filtros
          </Button>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {definiciones.map((definicion) => {
          const valorActual = searchParams.get(definicion.clave) ?? "";

          return (
            <div key={definicion.clave} className="flex flex-col gap-1.5">
              <Label
                htmlFor={`filtro-${definicion.clave}`}
                className="text-xs font-semibold text-foreground"
              >
                {definicion.etiqueta}
              </Label>
              <Select
                value={valorActual}
                onValueChange={(valor) => escribir(definicion.clave, valor)}
              >
                <SelectTrigger
                  id={`filtro-${definicion.clave}`}
                  className="min-h-11"
                >
                  <SelectValue
                    placeholder={definicion.etiqueta}
                    className="text-foreground"
                  />
                </SelectTrigger>
                <SelectContent>
                  {definicion.opciones.map((opcion) => (
                    <SelectItem key={opcion.valor} value={opcion.valor}>
                      {opcion.etiqueta}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          );
        })}
      </div>
    </div>
  );
}
