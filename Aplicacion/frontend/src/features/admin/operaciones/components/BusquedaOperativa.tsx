"use client";

import { Search } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export interface BusquedaOperativaProps {
  /**
   * EVERY query parameter of the current URL.
   *
   * The search lives in the URL with the rest of the filters, so a search can
   * be shared and survives a reload (`GOV-02-RB-03b`).
   */
  parametros: Record<string, string>;
  /** The name of the field, in the words of the operator. */
  etiqueta: string;
  /** The hint of the field. */
  placeholder?: string;
  /** The query parameter of the search. */
  clave?: string;
  className?: string;
}

/**
 * BusquedaOperativa - the free-text search of an operational list.
 *
 * It is the `q` parameter of the contract of the administrative lists
 * (`RT-PG-04` · `P-11`). The browser NEVER filters the list on its own: it
 * writes the query and the server answers.
 */
export function BusquedaOperativa({
  parametros,
  etiqueta,
  placeholder,
  clave = "q",
  className,
}: BusquedaOperativaProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [valor, setValor] = useState(parametros[clave] ?? "");

  function buscar(texto: string) {
    const siguiente: Record<string, string> = { ...parametros };

    if (texto.trim() === "") {
      delete siguiente[clave];
    } else {
      siguiente[clave] = texto.trim();
    }

    delete siguiente.page;

    const query = new URLSearchParams(siguiente).toString();
    router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  return (
    <form
      role="search"
      className={cn("flex flex-col gap-2 sm:flex-row sm:items-end", className)}
      onSubmit={(evento) => {
        evento.preventDefault();
        buscar(valor);
      }}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <label
          htmlFor="busqueda-operativa"
          className="text-xs font-semibold text-muted-foreground"
        >
          {etiqueta}
        </label>
        <Input
          id="busqueda-operativa"
          type="search"
          value={valor}
          placeholder={placeholder}
          className="min-h-11"
          onChange={(evento) => setValor(evento.target.value)}
        />
      </div>
      <Button type="submit" className="min-h-11">
        <Search className="size-4" aria-hidden="true" />
        Buscar
      </Button>
    </form>
  );
}
