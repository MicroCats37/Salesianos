"use client";

import { gsap } from "gsap";
import { Minus, Package, Plus, TriangleAlert, Trophy } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useGSAP } from "@/hooks/system/use-gsap";
import { cn } from "@/lib/utils";
import type { AltaInscripcionFormData } from "../schemas/alta-inscripcion.schema";
import type {
  CotizacionPaquete,
  PaqueteCatalogo,
} from "../types/inscripcion.types";
import { precioNumerico, precioOptimista } from "../utils/cotizacion-optimista";
import { esPaqueteDeVariasDisciplinas } from "../utils/paquete-copy";
import { PaqueteComercialCard } from "./PaqueteComercialCard";

export interface PasoPaqueteProps {
  /** The packages of the catalogue, as the server publishes them. */
  paquetes: readonly PaqueteCatalogo[];
  /** Whether the catalogue is still travelling. */
  cargando: boolean;
  /** The message of a recoverable failure, verbatim from the server. */
  error: string | null;
  /** The action that asks for the catalogue again. */
  onReintentar?: () => void;
  /** The last quotation of the server, when it already arrived. */
  cotizacion: CotizacionPaquete | null;
  /** Whether a quotation is travelling. */
  cotizacionCargando: boolean;
  /** The message of a failed quotation, verbatim from the server. */
  cotizacionError: string | null;
}

type FiltroPaquete = "paquete" | "disciplina";

const FILTROS: FiltroPaquete[] = ["paquete", "disciplina"];

const ETIQUETAS_FILTRO: Record<FiltroPaquete, string> = {
  paquete: "Paquete",
  disciplina: "Disciplina",
};

/**
 * PasoPaquete - the first step of the wizard.
 *
 * It is COPIED from the previous frontend (`frontend/src/features/
 * inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx`) and
 * adapted to the contract of the target backend:
 *
 * - the filter is a VIEW grouping (a package of several disciplines against a
 *   package of one) and it decides NOTHING: the price, the cupos and the
 *   teams are the server's;
 * - the quantity and the total of the card come from the QUOTATION of the
 *   server, never from a multiplication in the browser;
 * - the entrance of the cards is a stagger and it respects the reduced
 *   motion.
 */
export function PasoPaquete(props: PasoPaqueteProps) {
  const paquetes = props.paquetes;
  const cargando = props.cargando;
  const error = props.error;
  const onReintentar = props.onReintentar;
  const { cotizacion, cotizacionCargando, cotizacionError } = props;

  const contexto = useFormContext<AltaInscripcionFormData>();
  const setValue = contexto.setValue;
  const catalogoRef = useRef<HTMLDivElement>(null);

  const paqueteId = useWatch({
    control: contexto.control,
    name: "paquete_id" as const,
  });
  const cantidad = useWatch({
    control: contexto.control,
    name: "cantidad" as const,
  });

  const [filtro, setFiltro] = useState<FiltroPaquete>("paquete");

  /**
   * The quantity of EACH package.
   *
   * It lives here and not in the card because the quotation depends on it:
   * one quotation belongs to one package AND one quantity.
   */
  const [cantidades, setCantidades] = useState<Record<string, number>>({});

  /**
   * The mirror of the quantities.
   *
   * The stepper reads the quantity from a prop: two clicks in the same React
   * batch would compute the same "next" value and one of them would be
   * lost. The ref always holds the latest value.
   */
  const cantidadesRef = useRef<Record<string, number>>({});

  const porId = useMemo(
    () => new Map(paquetes.map((paquete) => [paquete.id, paquete])),
    [paquetes],
  );

  const paqueteSeleccionado = paqueteId ? (porId.get(paqueteId) ?? null) : null;

  const minimo = paqueteSeleccionado?.minimo_compra_inicial ?? 1;

  /**
   * The quantity is INITIALIZED at the minimum of the package and it never
   * falls below it: the stepper is disabled at the floor and the field is
   * corrected when the package changes.
   */
  useEffect(() => {
    if (!paqueteSeleccionado) return;
    if ((cantidad ?? minimo) >= minimo) return;
    setValue("cantidad", minimo, { shouldDirty: true });
  }, [paqueteSeleccionado, cantidad, minimo, setValue]);

  const conteos = useMemo(
    () => ({
      paquete: paquetes.filter(esPaqueteDeVariasDisciplinas).length,
      disciplina: paquetes.filter(
        (paquete) => !esPaqueteDeVariasDisciplinas(paquete),
      ).length,
    }),
    [paquetes],
  );

  // A filter with nothing in it is a dead end: it jumps to the first one
  // that has packages.
  useEffect(() => {
    if (conteos[filtro] > 0) return;

    const primeroConDatos = FILTROS.find((opcion) => conteos[opcion] > 0);
    if (primeroConDatos && primeroConDatos !== filtro) {
      setFiltro(primeroConDatos);
    }
  }, [conteos, filtro]);

  const visibles = useMemo(
    () =>
      paquetes.filter((paquete) =>
        filtro === "paquete"
          ? esPaqueteDeVariasDisciplinas(paquete)
          : !esPaqueteDeVariasDisciplinas(paquete),
      ),
    [paquetes, filtro],
  );

  const cantidadDe = useCallback(
    (id: string) => cantidades[id] ?? porId.get(id)?.minimo_compra_inicial ?? 1,
    [cantidades, porId],
  );

  /**
   * Move the quantity of ONE package.
   *
   * The floor is the commercial minimum that the package DECLARES: the
   * stepper never goes below it.
   */
  const cambiarCantidad = useCallback(
    (id: string, delta: number) => {
      const paquete = porId.get(id);
      const piso = paquete?.minimo_compra_inicial ?? 1;
      const base = cantidadesRef.current[id] ?? piso;
      const siguiente = Math.max(base + delta, piso);

      cantidadesRef.current = { ...cantidadesRef.current, [id]: siguiente };
      setCantidades(cantidadesRef.current);

      if (id === paqueteId) {
        setValue("cantidad", siguiente, { shouldDirty: true });
      }
    },
    [porId, paqueteId, setValue],
  );

  /**
   * The entrance of the catalogue.
   *
   * The cards arrive in reading order: a short stagger that says "this is a
   * catalogue you can compare", and not a jump. It is a REVEAL (opacity and
   * a few pixels), it never animates a height, and it is skipped when the
   * visitor asked for reduced motion.
   */
  useGSAP(
    () => {
      const catalogo = catalogoRef.current;
      if (!catalogo) return;

      const tarjetas = catalogo.querySelectorAll("[data-paquete-card]");
      if (tarjetas.length === 0) return;

      const media = gsap.matchMedia();

      media.add(
        { motionReducido: "(prefers-reduced-motion: reduce)" },
        (contexto) => {
          const condiciones = contexto.conditions as {
            motionReducido?: boolean;
          };

          if (condiciones.motionReducido) {
            gsap.set(tarjetas, { autoAlpha: 1, y: 0, clearProps: "all" });
            return;
          }

          gsap.fromTo(
            tarjetas,
            { autoAlpha: 0, y: 20 },
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.5,
              stagger: 0.08,
              ease: "power3.out",
              clearProps: "opacity,visibility,transform",
            },
          );
        },
      );

      return () => {
        media.revert();
      };
    },
    { scope: catalogoRef, dependencies: [visibles.length, filtro] },
  );

  /**
   * Choose a package.
   *
   * The QUANTITY of the new package starts at ITS OWN commercial minimum,
   * and the pending quotation of the previous package is dropped: the
   * wizard asks the server again for the new combination.
   */
  const seleccionar = useCallback(
    (id: string) => {
      const paquete = porId.get(id);
      const piso = paquete?.minimo_compra_inicial ?? 1;
      const cantidadNueva = cantidadesRef.current[id] ?? piso;

      cantidadesRef.current = { ...cantidadesRef.current, [id]: cantidadNueva };
      setCantidades(cantidadesRef.current);

      setValue("paquete_id", id, { shouldDirty: true });
      setValue("cantidad", cantidadNueva, { shouldDirty: true });
    },
    [porId, setValue],
  );

  if (cargando) {
    return (
      <div className="flex flex-col gap-3" aria-busy="true">
        <span className="sr-only">Cargando los paquetes disponibles</span>
        {[0, 1, 2].map((indice) => (
          <div
            key={indice}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-destructive/45 bg-destructive/10">
        <TriangleAlert className="size-4 text-destructive" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          No pudimos leer los paquetes
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          {error}
        </AlertDescription>
        {onReintentar ? (
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onReintentar}
              className="min-h-11"
            >
              Reintentar
            </Button>
          </div>
        ) : null}
      </Alert>
    );
  }

  if (paquetes.length === 0) {
    return (
      <RouteEmptyState
        icon={TriangleAlert}
        title="No hay paquetes disponibles en esta edición"
        description="El catálogo no publica ningún paquete con precio vigente. Cuando la edición abra su venta, los paquetes aparecerán aquí."
      />
    );
  }

  return (
    <fieldset className="flex flex-col gap-4">
      <legend className="text-sm font-semibold text-foreground">
        Elige el paquete que se contrata
      </legend>

      {/*
       * The filter: the pill is the gesture that says "this is a tab", and it
       * is the same one that the previous frontend had. It is POSITIONED
       * with `left` and not with a transform, so the page never animates a
       * movement: the pill changes its place and nothing else moves.
       */}
      <div
        role="tablist"
        aria-label="Tipo de paquete"
        className="relative flex w-full items-center rounded-full bg-muted p-1"
      >
        <div
          aria-hidden="true"
          className="absolute top-1 bottom-1 rounded-full bg-primary shadow-[var(--elevation-md)]"
          style={{
            width: `calc(${100 / FILTROS.length}% - 0.5rem)`,
            left: filtro === "paquete" ? "0.25rem" : "50%",
          }}
        />
        {FILTROS.map((opcion) => {
          const activa = opcion === filtro;
          const vacio = conteos[opcion] === 0;
          const Icono = opcion === "paquete" ? Package : Trophy;

          return (
            <button
              key={opcion}
              type="button"
              role="tab"
              aria-selected={activa}
              disabled={vacio}
              onClick={() => !vacio && setFiltro(opcion)}
              className={cn(
                "relative z-10 flex min-h-11 flex-1 items-center justify-center gap-2 rounded-full px-2 py-2 text-xs font-semibold transition-colors duration-(--motion-duration-fast)",
                vacio && "cursor-not-allowed opacity-50",
                activa
                  ? "text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icono className="size-4" aria-hidden="true" />
              {ETIQUETAS_FILTRO[opcion]}
              <span
                className={cn(
                  "ml-1 inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums",
                  activa
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : "bg-muted-foreground/15 text-muted-foreground",
                )}
              >
                {conteos[opcion]}
              </span>
            </button>
          );
        })}
      </div>

      <div
        ref={catalogoRef}
        className="grid items-stretch gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        {visibles.map((paquete) => {
          const cantidadPaquete = cantidadDe(paquete.id);
          const esSeleccionado = paquete.id === paqueteId;

          /*
           * The card ALWAYS shows a total: the projection of the catalogue
           * price while the quotation travels and the answer of the server
           * when it confirms THIS package and THIS quantity. The number
           * never blinks between "no price" and "server price".
           */
          const precio = precioOptimista({
            cotizacion,
            paqueteId: paquete.id,
            cantidad: cantidadPaquete,
            precioUnitarioCatalogo: precioNumerico(paquete.precio.monto),
          });

          return (
            <PaqueteComercialCard
              key={paquete.id}
              paquete={paquete}
              selected={esSeleccionado}
              onSelect={() => seleccionar(paquete.id)}
              precioCalculado={{
                total: `${precio.total.toFixed(2)} ${paquete.precio.moneda}`,
                unitario: `${precio.precioUnitario.toFixed(2)} ${paquete.precio.moneda} x integrante`,
                cantidad: cantidadPaquete,
                pendiente: esSeleccionado && cotizacionCargando,
              }}
              footer={
                esSeleccionado ? (
                  <div className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3">
                    <span className="flex flex-col items-center leading-tight">
                      <span className="text-eyebrow-brand text-muted-foreground">
                        Cantidad
                      </span>
                      <span className="text-caption text-muted-foreground">
                        Mínimo {paquete.minimo_compra_inicial}
                      </span>
                    </span>

                    <span className="flex items-center justify-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        aria-label="Disminuir la cantidad de personas"
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          cambiarCantidad(paquete.id, -1);
                        }}
                        disabled={
                          cantidadPaquete <= paquete.minimo_compra_inicial
                        }
                        className="size-10 shrink-0 rounded-full"
                      >
                        <Minus className="size-4" aria-hidden="true" />
                      </Button>

                      <output
                        aria-live="polite"
                        className="min-w-12 text-center text-lg font-bold tabular-nums text-foreground"
                      >
                        {cantidadPaquete}
                      </output>

                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        aria-label="Aumentar la cantidad de personas"
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          cambiarCantidad(paquete.id, 1);
                        }}
                        className="size-10 shrink-0 rounded-full"
                      >
                        <Plus className="size-4" aria-hidden="true" />
                      </Button>
                    </span>
                  </div>
                ) : null
              }
            />
          );
        })}
      </div>

      {cotizacionError ? (
        <Alert className="border-destructive/45 bg-destructive/10">
          <TriangleAlert
            className="size-4 text-destructive"
            aria-hidden="true"
          />
          <AlertTitle className="text-foreground">
            No pudimos cotizar este paquete
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            {cotizacionError}
          </AlertDescription>
        </Alert>
      ) : null}
    </fieldset>
  );
}
