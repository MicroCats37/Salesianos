"use client";

import { CalendarRange, Layers } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { ShellErrorState } from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import { useEdicionActual } from "../hooks/useEdicionActual";

/**
 * The dates of an edition are printed in UTC.
 *
 * The backend sends a DATE (`YYYY-MM-DD`), not an instant: it has no time
 * zone and no hour. Parsing it as UTC and printing it in UTC keeps the same
 * calendar day the backend published. Printing it in the local zone would move
 * the day for anybody west of Greenwich.
 */
const FECHA = new Intl.DateTimeFormat("es-PE", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/**
 * `EdicionActualPanel` — the edition that the backend publishes.
 *
 * PUB-02 reads the CURRENT EDITION from `GET /ediciones/actual` (`RT-ED-01`).
 * Before API-01 this page drew the configuration of the product from a
 * provisional fixture; now it draws the edition the server resolves, with the
 * honest states of the state matrix:
 *
 * - `S-01` loading: a skeleton with the geometry of the block.
 * - `S-02` empty: there is no published edition yet.
 * - `S-04` recoverable error: the message of the backend, verbatim, and the
 *   action that retries the read.
 *
 * The frontend NEVER resolves the edition by itself and NEVER shows a
 * previous edition as if it were the current one.
 */
export function EdicionActualPanel() {
  const { data, isPending, isError, error, refetch } = useEdicionActual();

  if (isPending) {
    return (
      <div
        className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
        aria-busy="true"
      >
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
    );
  }

  if (isError) {
    const status = (error as { status?: number } | null)?.status;

    // `404` is a DECISION of the backend: there is no published edition. It is
    // not a failure of the connection and it must not look like one.
    if (status === 404) {
      return (
        <RouteEmptyState
          icon={CalendarRange}
          title="Todavía no hay una edición publicada"
          description="El backend todavía no ha publicado una edición para este evento. Cuando la publique, aquí se verá su nombre, sus fechas y los módulos que tenga habilitados."
        />
      );
    }

    return (
      <ShellErrorState
        title="No pudimos leer la edición vigente"
        description={
          (error as { message?: string } | null)?.message ??
          "Vuelve a intentarlo en unos segundos."
        }
        accion={{ label: "Reintentar", onClick: () => void refetch() }}
        className="border-border bg-surface-raised"
      />
    );
  }

  if (!data) {
    return (
      <RouteEmptyState
        icon={CalendarRange}
        title="No hay una edición vigente"
        description="La edición vigente todavía no está disponible. Vuelve a intentarlo en unos segundos."
      />
    );
  }

  const modulosHabilitados = data.modulos.filter((modulo) => modulo.habilitado);
  const fechas =
    data.fecha_inicio && data.fecha_fin
      ? `${FECHA.format(new Date(data.fecha_inicio))} — ${FECHA.format(new Date(data.fecha_fin))}`
      : data.fecha_inicio
        ? `Desde el ${FECHA.format(new Date(data.fecha_inicio))}`
        : data.fecha_fin
          ? `Hasta el ${FECHA.format(new Date(data.fecha_fin))}`
          : null;

  return (
    <div className="glow-brand flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4">
      <div className="flex flex-col gap-1">
        <span
          className="rule-gold block h-0.5 w-8 rounded-full"
          aria-hidden="true"
        />
        <span className="text-caption text-muted-foreground">
          La edición vigente
        </span>
        <h3 className="text-section-title text-foreground">
          {data.nombre} · {data.anio}
        </h3>
        <p className="text-caption text-muted-foreground">
          {data.evento_nombre}
        </p>
      </div>

      {fechas ? (
        <p className="flex items-center gap-2 text-caption text-muted-foreground">
          <CalendarRange className="size-4 shrink-0" aria-hidden="true" />
          {fechas}
        </p>
      ) : null}

      <div className="flex flex-col gap-1.5">
        <span className="flex items-center gap-2 text-caption text-muted-foreground">
          <Layers className="size-4 shrink-0" aria-hidden="true" />
          Módulos de esta edición
        </span>
        {modulosHabilitados.length > 0 ? (
          <ul className="flex flex-wrap gap-2">
            {modulosHabilitados.map((modulo) => (
              <li
                key={modulo.clave}
                className="rounded-[var(--radius-md)] border border-border bg-surface-recessed px-2 py-1 text-caption text-foreground"
              >
                {modulo.nombre}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-caption text-muted-foreground">
            Esta edición todavía no tiene módulos habilitados.
          </p>
        )}
      </div>
    </div>
  );
}
