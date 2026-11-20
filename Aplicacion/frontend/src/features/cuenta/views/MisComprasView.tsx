import { ShoppingBag } from "lucide-react";
import { Suspense } from "react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarraFiltros,
  ListaCompras,
  SinResultadosConFiltros,
} from "../components";
import { etiquetaOrigen, ORIGENES } from "../components/ListaCompras";
import type { CompraResumen, EstadoVista } from "../types/cuenta.types";

/** The keys of the filters of the list, in the URL. */
export const CLAVES_FILTRO_COMPRAS = ["origen"] as const;

export interface MisComprasViewProps {
  /** The state of the list. */
  estado?: EstadoVista;
  /** Every purchase the account has, BEFORE the filters. */
  compras?: CompraResumen[];
  /** The filters that are active, read from the URL by the page. */
  filtros?: Record<string, string | undefined>;
}

/**
 * ACCOUNT-04 - the purchases of the responsible.
 *
 * The purchase and the payment are two different things: a purchase may be
 * paid, pending or cancelled, and only the backend knows which one is
 * which. The list shows the verdict, never a recomputation.
 *
 * The purchases are grouped by origin: a registration, a pass and a store
 * product are three different things and they never travel in one checkout
 * (`GOV-02-RB-02a`).
 */
export function MisComprasView({
  estado = "sin-datos",
  compras = [],
  filtros = {},
}: MisComprasViewProps) {
  const hayCompras = compras.length > 0;

  const visibles = compras.filter((compra) => {
    const origen = filtros.origen;
    if (origen && compra.origen !== origen) return false;
    return true;
  });

  const grupos = ORIGENES.map((origen) => ({
    ...origen,
    compras: visibles.filter((compra) => compra.origen === origen.valor),
  })).filter((grupo) => grupo.compras.length > 0);

  const opcionesOrigen = Array.from(
    new Set(compras.map((compra) => compra.origen)),
  ).map((valor) => ({
    valor,
    etiqueta: etiquetaOrigen(valor),
  }));

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="ACCOUNT-04"
        tone="hero"
        title="Tus compras"
        description="Las compras de la edición con su estado de pago, su importe y la fecha en que se realizaron."
      />

      {estado === "sin-permiso" ? (
        <ShellPermissionDenied
          title="No podemos leer tus compras"
          className="border-border bg-surface-raised"
        />
      ) : null}

      {estado === "cargando" ? (
        <div
          className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          aria-busy="true"
        >
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar tus compras"
          description="No pudimos leer tus compras en este momento. Vuelve a intentarlo en unos segundos."
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={ShoppingBag}
          title="Todavía no tienes compras registradas"
          description="Aquí aparecerán las compras de inscripción, pases y tienda con su importe, estado de pago y fecha."
        />
      ) : null}

      {estado === "listo" ? (
        <>
          {hayCompras ? (
            <Suspense
              fallback={
                <div
                  className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
                  aria-busy="true"
                >
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-11 w-full sm:w-64" />
                </div>
              }
            >
              <BarraFiltros
                definiciones={[
                  {
                    clave: "origen",
                    etiqueta: "Origen",
                    opciones: opcionesOrigen,
                  },
                ]}
              />
            </Suspense>
          ) : null}

          {hayCompras && visibles.length === 0 ? (
            <SinResultadosConFiltros
              claves={[...CLAVES_FILTRO_COMPRAS]}
              totalSinFiltrar={compras.length}
            />
          ) : null}

          {grupos.map((grupo) => (
            <section key={grupo.valor} className="flex flex-col gap-3">
              <h2 className="text-section-title text-foreground">
                {grupo.etiqueta}
              </h2>
              <ListaCompras compras={grupo.compras} />
            </section>
          ))}
        </>
      ) : null}
    </div>
  );
}
