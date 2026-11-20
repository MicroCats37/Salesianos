import { ClipboardList, Plus } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { ShellErrorState, ShellPermissionDenied } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RUTAS } from "@/lib/routes";
import { BarraFiltros, ListaInscripciones, SinResultadosConFiltros } from "../components";
import type { EstadoVista, InscripcionResumen } from "../types/cuenta.types";

/** The keys of the filters of the list, in the URL. */
export const CLAVES_FILTRO_INSCRIPCIONES = ["edicion", "estado"] as const;

export interface MisInscripcionesViewProps {
  /** The state of the list. */
  estado?: EstadoVista;
  /** Every registration the account has, BEFORE the filters. */
  inscripciones?: InscripcionResumen[];
  /** The filters that are active, read from the URL by the page. */
  filtros?: Record<string, string | undefined>;
}

/**
 * ACCOUNT-02 - the registrations of the responsible.
 *
 * The list is a LIST, not a grid of cards: the responsible reads her own
 * registrations one after the other and compares them, and a row compares
 * better than a tile.
 *
 * The filters live in the URL, so a filtered list can be shared and
 * restored with the back button. They are only drawn when there is
 * something to filter.
 */
export function MisInscripcionesView({
  estado = "sin-datos",
  inscripciones = [],
  filtros = {},
}: MisInscripcionesViewProps) {
  const hayRegistros = inscripciones.length > 0;

  const visibles = inscripciones.filter((inscripcion) => {
    const edicion = filtros.edicion;
    const estadoFiltro = filtros.estado;

    if (edicion && inscripcion.edicion !== edicion) return false;
    if (estadoFiltro && inscripcion.veredicto.estado.codigo !== estadoFiltro) {
      return false;
    }

    return true;
  });

  const opcionesEdicion = Array.from(
    new Map(inscripciones.map((i) => [i.edicion, i.edicion])).values(),
  ).map((valor) => ({ valor, etiqueta: valor }));

  const opcionesEstado = Array.from(
    new Map(
      inscripciones.map((i) => [
        i.veredicto.estado.codigo,
        { valor: i.veredicto.estado.codigo, etiqueta: i.veredicto.estado.etiqueta },
      ]),
    ).values(),
  );

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="ACCOUNT-02"
        title="Tus inscripciones"
        description="Cada inscripción de la edición con su estado, el paquete que contrataste y las personas y equipos que lleva."
        actions={
          <Button asChild className="min-h-11">
            <Link href={RUTAS.cuenta.inscripcion}>
              <Plus className="size-4" aria-hidden="true" />
              Nueva inscripción
            </Link>
          </Button>
        }
      />

      {estado === "sin-permiso" ? (
          <ShellPermissionDenied
            title="No podemos leer tus inscripciones"
            className="border-border bg-surface-raised"
          />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar tus inscripciones"
          description="No pudimos leer tus registros en este momento. Vuelve a intentarlo en unos segundos."
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={ClipboardList}
          title="Todavía no tienes inscripciones registradas"
          description="Las inscripciones se leen del servicio de la cuenta. Cuando la integración esté disponible, aquí se listarán con su estado, su paquete y sus contadores, y se podrá entrar al detalle de cada una."
          action={
            <Button asChild className="min-h-11">
              <Link href={RUTAS.cuenta.inscripcion}>Crear la primera</Link>
            </Button>
          }
        />
      ) : null}

      {estado === "listo" ? (
        <>
          {hayRegistros ? (
            <Suspense
              fallback={
                <div
                  className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
                  aria-busy="true"
                >
                  <Skeleton className="h-4 w-24" />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Skeleton className="h-11 w-full" />
                    <Skeleton className="h-11 w-full" />
                  </div>
                </div>
              }
            >
              <BarraFiltros
                definiciones={[
                  { clave: "edicion", etiqueta: "Edición", opciones: opcionesEdicion },
                  { clave: "estado", etiqueta: "Estado", opciones: opcionesEstado },
                ]}
              />
            </Suspense>
          ) : null}

          {hayRegistros && visibles.length === 0 ? (
            <SinResultadosConFiltros
              claves={[...CLAVES_FILTRO_INSCRIPCIONES]}
              totalSinFiltrar={inscripciones.length}
            />
          ) : null}

          {visibles.length > 0 ? (
            <ListaInscripciones inscripciones={visibles} />
          ) : null}
        </>
      ) : null}
    </div>
  );
}

