import type { ReactNode } from "react";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import type { EstadoSuperficie } from "../types/operaciones.types";

export interface MarcoOperativoProps<T> {
  /** The state of the surface. */
  estado: EstadoSuperficie<T>;
  /** What the surface shows when the data source is not connected yet. */
  sinDatos: ReactNode;
  /** What the surface shows while the read is in flight. */
  cargando: ReactNode;
  /** What the surface shows when the read failed. */
  error?: ReactNode;
  /** What the surface shows when the backend refused the read. */
  sinPermiso?: ReactNode;
  /** The composition of the surface when the data arrived. */
  children: (datos: T) => ReactNode;
}

/**
 * MarcoOperativo - the state switch of an operational surface.
 *
 * The ten states of `SH-03` are not optional decoration: an operational
 * screen that only knows how to show data is a screen that breaks the day
 * the backend answers with a 403.
 *
 * - `sin-datos` is the DEFAULT: the route is not connected yet.
 * - `cargando` never invents a remaining time.
 * - `error` shows the message of the backend VERBATIM (`SH-03` §2).
 * - `sin-permiso` explains that the ACCOUNT lacks the permission; it never
 *   proposes a way around it.
 */
export function MarcoOperativo<T>({
  estado,
  sinDatos,
  cargando,
  error,
  sinPermiso,
  children,
}: MarcoOperativoProps<T>) {
  switch (estado.estado) {
    case "cargando":
      return <>{cargando}</>;
    case "error":
      return (
        <>
          {error ?? (
            <ShellErrorState
              title="No pudimos cargar esta información"
              description={estado.mensaje}
              className="min-h-11"
            />
          )}
        </>
      );
    case "sin-permiso":
      return (
        <>
          {sinPermiso ?? (
            <ShellPermissionDenied
              title="No tienes permiso para ver esto"
              description={estado.mensaje}
            />
          )}
        </>
      );
    case "sin-datos":
      return <>{sinDatos}</>;
    case "listo":
      return <>{children(estado.datos)}</>;
  }
}
