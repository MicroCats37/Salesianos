"use client";

import { gsap } from "gsap";
import { Minus, Package, Plus, Trophy } from "lucide-react";
import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useFormContext } from "react-hook-form";
import {
  PaqueteComercialCard,
  type PrecioCalculado,
} from "@/components/paquetes/PaqueteComercialCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useCotizacion } from "../../hooks/useCotizacion";
import { usePaquetes } from "../../hooks/useInscripcionCatalogs";
import type { CotizacionResponse } from "../../schemas/cotizacion.schema";
import type { InscripcionFormData } from "../../schemas/inscripcion.schema";
import type { PaqueteListContract } from "../../schemas/paquete.schema";
import { precioOptimista } from "../../utils/cotizacion.optimista";

type TipoFilter = "PACK" | "DISCIPLINA";

// ── Tab config ────────────────────────────────────────────────────────────────

const TAB_ORDER: TipoFilter[] = ["PACK", "DISCIPLINA"];

const TAB_LABELS: Record<TipoFilter, string> = {
  PACK: "Paquete",
  DISCIPLINA: "Disciplina",
};

/** Debounce before asking the backend for a new quote. */
const COTIZACION_DEBOUNCE_MS = 400;

function TabIcon({ tab }: { tab: TipoFilter }) {
  if (tab === "PACK") return <Package className="size-4" />;
  return <Trophy className="size-4" />;
}

interface SmartPaqueteCardsFieldProps {
  fieldName: "paquete_id";
  containerClassName?: string;
}

interface PaqueteCardProps {
  paquete: PaqueteListContract;
  isSelected: boolean;
  cantidad: number;
  /** Only the selected card receives the quote — the rest always get null. */
  cotizacion: CotizacionResponse | null;
  onCantidadChange: (paqueteId: string, delta: number) => void;
  onSelect: (paqueteId: string) => void;
}

// ── PaqueteCard ──────────────────────────────────────────────────────────────

/**
 * One package card.
 *
 * Memoized on purpose: the quantity and the quote of ONE package must not
 * re-render the other cards of the row.
 */
const PaqueteCard = memo(function PaqueteCard({
  paquete,
  isSelected,
  cantidad,
  cotizacion,
  onCantidadChange,
  onSelect,
}: PaqueteCardProps) {
  /**
   * The card always shows a total: the server answer when it confirms this
   * package and quantity, a projection of the last known unit price while the
   * request is in flight. The number never disappears and never blinks.
   */
  const precio = precioOptimista({
    cotizacion,
    paqueteId: paquete.id,
    cantidad,
    precioPreventa: paquete.precio_preventa,
    precioRegular: paquete.precio_regular,
  });

  /**
   * The computed price is shown whenever the card has a quantity of its own:
   * when it is selected (that is what the user is buying) AND when the user
   * moved its stepper without selecting it. A card left at the catalog
   * minimum keeps the static catalog layout.
   */
  const precioCalculado: PrecioCalculado | null =
    isSelected || cantidad !== paquete.cantidad_minima_compra
      ? {
          total: precio.total,
          unitario: precio.precioUnitario,
          totalRegular: precio.totalRegular,
          cantidad,
          pendiente: isSelected && !precio.confirmada,
        }
      : null;

  const footer = (
    <div className="rounded-xl border border-slate-200 bg-[#f8fafc] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-wider text-[#626195]">
            Cantidad
          </p>
          <p className="text-[11px] font-semibold text-[#626195]">
            Mínimo {paquete.cantidad_minima_compra} integrantes
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Disminuir cantidad"
            onClick={(event) => {
              event.stopPropagation();
              onCantidadChange(paquete.id, -1);
            }}
            disabled={cantidad <= paquete.cantidad_minima_compra}
            className="size-8 rounded-full border-slate-300"
          >
            <Minus className="size-4" />
          </Button>
          <span className="w-8 text-center text-lg font-black text-[#17214b]">
            {cantidad}
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Aumentar cantidad"
            onClick={(event) => {
              event.stopPropagation();
              onCantidadChange(paquete.id, 1);
            }}
            className="size-8 rounded-full border-slate-300"
          >
            <Plus className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <PaqueteComercialCard
      paquete={paquete}
      variant={paquete.tipo}
      selected={isSelected}
      onSelect={() => onSelect(paquete.id)}
      precioCalculado={precioCalculado}
      footer={footer}
      className="package-card"
    />
  );
});

// ── SmartPaqueteCardsField ────────────────────────────────────────────────────

export function SmartPaqueteCardsField({
  fieldName,
  containerClassName,
}: SmartPaqueteCardsFieldProps) {
  const { data: paquetes, isLoading } = usePaquetes();
  const { watch, setValue } = useFormContext<InscripcionFormData>();
  const watchedPaqueteId = watch(fieldName);
  const containerRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<TipoFilter>("PACK");

  /**
   * Quantity per package.
   *
   * It lives here (not inside the card) because the quotation depends on it:
   * one quote belongs to one package + quantity.
   */
  const [cantidades, setCantidades] = useState<Record<string, number>>({});

  /**
   * Mirror of the quantity map.
   *
   * The stepper reads the quantity from a prop, so two clicks in the same
   * React batch would both compute the same "next" value and one of them
   * would be lost. The ref always holds the latest value.
   */
  const cantidadesRef = useRef<Record<string, number>>({});

  // A single quotation for the whole picker — see `useCotizacion`.
  const { cotizacion, cotizar, invalidate } = useCotizacion();

  const paquetesPorId = useMemo(
    () => new Map((paquetes ?? []).map((paquete) => [paquete.id, paquete])),
    [paquetes],
  );

  const paqueteSeleccionado = watchedPaqueteId
    ? (paquetesPorId.get(watchedPaqueteId) ?? null)
    : null;
  const paqueteId = paqueteSeleccionado?.id ?? null;
  const cantidadSeleccionada = paqueteSeleccionado
    ? (cantidades[paqueteSeleccionado.id] ??
      paqueteSeleccionado.cantidad_minima_compra)
    : 0;

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-animate when the package list or filter changes.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".package-card",
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: "power3.out" },
      );
    }, container);
    return () => ctx.revert();
  }, [paquetes?.length, filter]);

  /**
   * Ask for a quote whenever the selected package or its quantity changes.
   *
   * The debounce collapses a burst of clicks into a single request, and the
   * card keeps showing the projected total meanwhile.
   */
  useEffect(() => {
    if (!paqueteId) return;
    const handle = setTimeout(() => {
      cotizar(paqueteId, cantidadSeleccionada);
    }, COTIZACION_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [paqueteId, cantidadSeleccionada, cotizar]);

  /**
   * Publish the confirmed quote to the form.
   *
   * Only a quote that matches the selected package AND the selected quantity
   * is written — a stale answer must never reach the purchase payload.
   */
  useEffect(() => {
    if (!cotizacion) return;
    if (cotizacion.paquete_id !== paqueteId) return;
    if (cotizacion.cantidad_cotizada !== cantidadSeleccionada) return;
    setValue("precio_unitario_cotizado", cotizacion.precio_unitario, {
      shouldDirty: true,
    });
    setValue("cotizacion_version", cotizacion.version, {
      shouldDirty: true,
    });
  }, [cotizacion, paqueteId, cantidadSeleccionada, setValue]);

  const filteredPaquetes = (paquetes ?? []).filter((p) => p.tipo === filter);

  const counts = useMemo<Record<TipoFilter, number>>(
    () => ({
      PACK: paquetes?.filter((p) => p.tipo === "PACK").length ?? 0,
      DISCIPLINA: paquetes?.filter((p) => p.tipo === "DISCIPLINA").length ?? 0,
    }),
    [paquetes],
  );

  // Si el filtro actual está vacío, salta automáticamente al primero con datos.
  useEffect(() => {
    if (counts[filter] === 0) {
      const firstWithData = TAB_ORDER.find((t) => counts[t] > 0);
      if (firstWithData && firstWithData !== filter) {
        setFilter(firstWithData);
      }
    }
  }, [counts, filter]);

  const cantidadDe = useCallback(
    (paqueteId: string) =>
      cantidades[paqueteId] ??
      paquetesPorId.get(paqueteId)?.cantidad_minima_compra ??
      0,
    [cantidades, paquetesPorId],
  );

  const handleCantidadChange = useCallback(
    (paqueteId: string, delta: number) => {
      const minimo = paquetesPorId.get(paqueteId)?.cantidad_minima_compra ?? 1;
      const base = cantidadesRef.current[paqueteId] ?? minimo;
      const next = Math.max(minimo, base + delta);
      cantidadesRef.current = { ...cantidadesRef.current, [paqueteId]: next };
      setCantidades(cantidadesRef.current);
      if (paqueteId === watchedPaqueteId) {
        setValue("cantidad", next, { shouldDirty: true });
      }
    },
    [paquetesPorId, watchedPaqueteId, setValue],
  );

  const handleSelect = useCallback(
    (paqueteId: string) => {
      const yaSeleccionado = paqueteId === watchedPaqueteId;
      setValue("paquete_id", paqueteId, { shouldDirty: true });

      if (yaSeleccionado) return;

      // Switching package: the pending quote belongs to the previous package, so
      // it is dropped and re-requested for the new one.
      //
      // The quantity is read from the REF on purpose: reading it from the
      // state would rebuild this callback on every quantity change and break
      // the memoization of the sibling cards.
      const minimo = paquetesPorId.get(paqueteId)?.cantidad_minima_compra ?? 1;
      const cantidad = cantidadesRef.current[paqueteId] ?? minimo;
      setValue("cantidad", cantidad, { shouldDirty: true });
      setValue("precio_unitario_cotizado", undefined, { shouldDirty: true });
      setValue("cotizacion_version", undefined, { shouldDirty: true });
      invalidate();
    },
    [paquetesPorId, invalidate, setValue, watchedPaqueteId],
  );

  return (
    <div ref={containerRef} className={cn("space-y-4", containerClassName)}>
      <div className="relative flex w-full items-center rounded-full bg-slate-100 p-1">
        <div
          className="absolute top-1 bottom-1 rounded-full bg-primary shadow-md transition-all duration-300 ease-out"
          style={{
            width: "calc(50% - 4px)",
            transform: `translateX(${filter === "PACK" ? "0" : "calc(100% + 4px)"})`,
          }}
        />
        {TAB_ORDER.map((tab) => {
          const active = filter === tab;
          const disabled = counts[tab] === 0;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => !disabled && setFilter(tab)}
              disabled={disabled}
              data-tab-active={tab}
              className={cn(
                "relative z-10 flex flex-1 items-center justify-center gap-2 rounded-full px-2 py-3 transition-all duration-300",
                disabled && "cursor-not-allowed opacity-50",
                active
                  ? "font-bold text-white"
                  : "text-slate-600 hover:text-slate-900",
              )}
            >
              <TabIcon tab={tab} />
              <span className="text-xs font-semibold uppercase tracking-wider">
                {TAB_LABELS[tab]}
              </span>
              <span
                className={cn(
                  "ml-1 inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                  active
                    ? "bg-white/20 text-white"
                    : "bg-slate-200 text-slate-600",
                )}
              >
                {counts[tab]}
              </span>
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3].map((item) => (
            <Skeleton
              key={item}
              className="h-[30rem] w-full rounded-2xl bg-slate-200"
            />
          ))}
        </div>
      ) : filteredPaquetes.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-500">
          No hay paquetes disponibles para este filtro.
        </p>
      ) : (
        <div className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {filteredPaquetes.map((paquete) => (
            <div key={paquete.id} className="h-full">
              <PaqueteCard
                paquete={paquete}
                isSelected={watchedPaqueteId === paquete.id}
                cantidad={cantidadDe(paquete.id)}
                cotizacion={watchedPaqueteId === paquete.id ? cotizacion : null}
                onCantidadChange={handleCantidadChange}
                onSelect={handleSelect}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
