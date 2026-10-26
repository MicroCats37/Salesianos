"use client";

import { ArrowDownAZ, Eraser, Search } from "lucide-react";
import type { MutableRefObject, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useIsMobileState } from "@/hooks/use-mobile";
import type { AdminOpcionOrden } from "../utils/admin.lista.utils";
import { AdminFiltrosSheet } from "./AdminFiltrosSheet";

/**
 * Cancels a pending publication of the free-text term.
 *
 * It lives OUTSIDE the component on purpose: a helper declared inside would
 * become a dependency of the effects that use it, and the reference of the
 * timer is already stable.
 */
function cancelarPublicacion(
  temporizador: MutableRefObject<ReturnType<typeof setTimeout> | null>,
) {
  if (temporizador.current) {
    clearTimeout(temporizador.current);
    temporizador.current = null;
  }
}

export interface AdminListaToolbarProps {
  /** Current free-text term (owned by the URL). */
  termino: string;
  /** Publishes a new free-text term. */
  onBuscar: (termino: string) => void;
  /** Ordering options of the resource — only whitelisted public fields. */
  opcionesOrden: AdminOpcionOrden[];
  /** Current ordering value. */
  orden: string;
  onCambiarOrden: (orden: string) => void;
  /** Whether a filter is narrowing the list. */
  hayFiltros: boolean;
  /** How many resource filters are active. */
  filtrosActivos: number;
  /** The "Limpiar filtros" action. */
  onLimpiarFiltros: () => void;
  /** The resource filters of the section. */
  children?: ReactNode;
}

/**
 * AdminListaToolbar — search, ordering and the resource filters.
 *
 * The free-text term is published with a delay: one keystroke must not
 * become one request. The term itself lives in the URL, so the delay is a
 * transport detail and never a different source of truth.
 *
 * Below 768px the resource filters live inside a sheet, so they are not even
 * in the DOM until the administrator opens them. The branch is decided in
 * JAVASCRIPT (`useIsMobileState`), not with a CSS class: a control that is
 * mounted and hidden is still a control in the DOM.
 */
export function AdminListaToolbar({
  termino,
  onBuscar,
  opcionesOrden,
  orden,
  onCambiarOrden,
  hayFiltros,
  filtrosActivos,
  onLimpiarFiltros,
  children,
}: AdminListaToolbarProps) {
  const [texto, setTexto] = useState(termino);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);
  const buscarRef = useRef(onBuscar);

  // `undefined` while the size of the viewport is unknown.
  const esMovil = useIsMobileState();

  // The publisher is kept in a reference: a publication that fires 400 ms
  // later must use the LATEST state of the list, never the one that was
  // current when the term was typed.
  useEffect(() => {
    buscarRef.current = onBuscar;
  }, [onBuscar]);

  // The URL is the authority: when it changes from the outside (the "Limpiar
  // filtros" action, the browser back button) the input follows it and any
  // pending publication is CANCELLED — an explicit clear must never be undone
  // by a term that was typed before it.
  useEffect(() => {
    cancelarPublicacion(temporizador);
    setTexto((actual) => (actual === termino ? actual : termino));
  }, [termino]);

  // A pending publication never outlives the component.
  useEffect(() => {
    return () => {
      cancelarPublicacion(temporizador);
    };
  }, []);

  function cambiarTexto(valor: string) {
    setTexto(valor);
    cancelarPublicacion(temporizador);
    temporizador.current = setTimeout(() => {
      temporizador.current = null;
      buscarRef.current(valor);
    }, 400);
  }

  function limpiar() {
    cancelarPublicacion(temporizador);
    setTexto("");
    onLimpiarFiltros();
  }

  return (
    <div className="card-elevated flex flex-col gap-4 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex-1">
          <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
            <Search className="size-3" />
            Buscar
          </span>
          <Input
            value={texto}
            onChange={(evento) => cambiarTexto(evento.target.value)}
            placeholder="Buscar por nombre, documento o referencia"
            aria-label="Buscar"
            className="h-9 rounded-xl bg-white text-xs font-medium"
          />
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div>
            <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
              <ArrowDownAZ className="size-3" />
              Ordenar por
            </span>
            <Select value={orden} onValueChange={onCambiarOrden}>
              <SelectTrigger
                className="h-9 w-full min-w-[13rem] rounded-xl bg-white text-xs font-bold"
                aria-label="Ordenar por"
              >
                <SelectValue placeholder="Ordenar por" />
              </SelectTrigger>
              <SelectContent>
                {opcionesOrden.map((opcion) => (
                  <SelectItem key={opcion.valor} value={opcion.valor}>
                    {opcion.etiqueta}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {esMovil === true ? (
            <AdminFiltrosSheet activeCount={filtrosActivos} onClear={limpiar}>
              {children}
            </AdminFiltrosSheet>
          ) : null}

          {hayFiltros && (
            <Button
              type="button"
              variant="ghost"
              onClick={limpiar}
              className="btn-brand-gradient btn-shine h-9 gap-2 rounded-full px-4 text-xs font-black uppercase tracking-wider"
            >
              <Eraser className="size-3.5" />
              Limpiar filtros
            </Button>
          )}
        </div>
      </div>

      {esMovil === false && children ? (
        <div className="grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2 lg:grid-cols-4">
          {children}
        </div>
      ) : null}

      {/*
        The size of the viewport is unknown (server render): the space of the
        inline filters is reserved so the list does not jump when the branch
        is resolved. 73px = the label + the control + the top border.
      */}
      {esMovil === undefined && children ? (
        <div
          aria-hidden="true"
          className="h-[73px] border-t border-slate-100"
        />
      ) : null}
    </div>
  );
}
