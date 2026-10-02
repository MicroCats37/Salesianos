"use client";

// Smart PaqueteCardsField — selecciona un paquete, muestra cards estilo
// "Paquetes de preinscripcion" del landing (ribbon, badge ELEGIBLE/FIJO,
// precio tachado + promo, descripcion, bullets, CTA, modulo de pago).

import { gsap } from "gsap";
import { Check, Package, Users } from "lucide-react";
import { useEffect, useRef } from "react";
import { Controller } from "react-hook-form";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { usePaquetes } from "../../hooks/useInscripcionCatalogs";
import type { PaqueteDisciplina } from "../../services/catalog.service";

interface SmartPaqueteCardsFieldProps {
  fieldName: "paquete_id";
  containerClassName?: string;
}

interface PaqueteCardProps {
  id: string;
  nombre: string;
  descripcion: string | null;
  precio_regular: number;
  precio_promocional: number | null;
  cantidad_maxima_participantes: number;
  cantidad_disciplinas_requeridas: number;
  disciplinas: PaqueteDisciplina[];
  isSelected: boolean;
  onSelect: () => void;
}

function PaqueteCard(card: PaqueteCardProps) {
  const cardRef = useRef<HTMLButtonElement>(null);
  const isElegible = card.cantidad_disciplinas_requeridas > 1;

  const bullets = [
    `Hasta ${card.cantidad_maxima_participantes} jugadores por equipo`,
    isElegible
      ? `Selecciona ${card.cantidad_disciplinas_requeridas} disciplinas de la oferta disponible`
      : `Selecciona ${card.cantidad_disciplinas_requeridas} disciplina de la oferta disponible`,
    "Validacion contra padron salesiano",
    "Soporte del Comite durante todo el proceso",
  ];

  return (
    <button
      ref={cardRef}
      type="button"
      onClick={card.onSelect}
      className={cn(
        "package-card relative flex h-full w-full flex-col rounded-[1.75rem] border bg-white p-6 text-left transition-all duration-300 shadow-xl ring-1 ring-[#312e8e]/10 hover:shadow-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500",
        card.isSelected
          ? "border-amber-500 ring-2 ring-amber-200"
          : "border-slate-200/80",
      )}
    >
      {/* Gold ribbon with package name */}
      <div className="absolute -top-4 left-1/2 -translate-x-1/2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400 px-4 py-1.5 text-xs font-black uppercase tracking-wider text-slate-900 shadow-lg">
          <Package className="size-3.5" />
          {card.nombre}
        </span>
      </div>

      {/* Header: nombre + badge modo */}
      <div className="mt-4 flex items-start justify-between gap-3">
        <h3 className="text-sm font-black uppercase tracking-wider text-[#312e8e]">
          {card.nombre}
        </h3>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-black uppercase tracking-wider",
            isElegible
              ? "bg-amber-400 text-slate-900"
              : "bg-[#312e8e]/10 text-[#312e8e]",
          )}
        >
          {isElegible ? "Elegible" : "Fijo"}
        </span>
      </div>

      {/* Price block */}
      <div className="mt-4">
        {card.precio_promocional ? (
          <>
            <p className="text-4xl font-black tracking-tight text-emerald-600">
              S/{card.precio_promocional.toFixed(2)}
            </p>
            <p className="text-xs text-slate-400 line-through">
              S/{card.precio_regular.toFixed(2)} regular
            </p>
          </>
        ) : (
          <p className="text-4xl font-black tracking-tight text-slate-900">
            S/{card.precio_regular.toFixed(2)}
          </p>
        )}
        <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
          por equipo
        </p>
      </div>

      {/* Description */}
      {card.descripcion && (
        <p className="mt-4 text-sm leading-6 text-slate-600">
          {card.descripcion}
        </p>
      )}

      {/* Disciplinas chips */}
      <div className="mt-4">
        <p className="text-[10px] font-black uppercase tracking-wider text-slate-500">
          Disciplinas disponibles
        </p>
        {card.disciplinas.length === 0 ? (
          <p className="text-xs text-slate-400 italic">
            Sin disciplinas configuradas
          </p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {card.disciplinas.slice(0, 5).map((d) => (
              <span
                key={d.disciplina_id}
                className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700"
              >
                {d.disciplina_nombre} ({d.disciplina_sigla})
              </span>
            ))}
            {card.disciplinas.length > 5 && (
              <span className="inline-flex items-center rounded-full bg-slate-50 px-2.5 py-0.5 text-xs text-slate-500">
                +{card.disciplinas.length - 5}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Features bullets */}
      <ul className="mt-5 space-y-2 text-sm text-slate-700">
        {bullets.map((b) => (
          <li key={b} className="flex items-start gap-2">
            <Check className="mt-0.5 size-4 shrink-0 text-emerald-500" />
            <span>{b}</span>
          </li>
        ))}
      </ul>

      {/* Capacity hint */}
      <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
        <Users className="size-3.5" />
        <span>Máx. {card.cantidad_maxima_participantes} participantes</span>
      </div>

      {/* Selection state (purely informational, no CTA needed here) */}
      {card.isSelected && (
        <div className="mt-4 flex items-center justify-center gap-2 rounded-full bg-emerald-50 py-2 text-xs font-black uppercase tracking-wider text-emerald-700">
          <Check className="size-4" />
          Paquete seleccionado
        </div>
      )}
    </button>
  );
}

export function SmartPaqueteCardsField({
  fieldName,
  containerClassName,
}: SmartPaqueteCardsFieldProps) {
  const { data: paquetes, isLoading } = usePaquetes();
  const containerRef = useRef<HTMLDivElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-animate when package list changes.
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
  }, [paquetes]);

  return (
    <div ref={containerRef} className={cn("space-y-3", containerClassName)}>
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3].map((i) => (
            <Skeleton
              key={i}
              className="h-48 w-full bg-slate-200 rounded-2xl"
            />
          ))}
        </div>
      ) : (
        <Controller
          name={fieldName}
          render={({ field }) => (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {(paquetes ?? []).map((p) => (
                <PaqueteCard
                  key={p.id}
                  id={p.id}
                  nombre={p.nombre}
                  descripcion={p.descripcion}
                  precio_regular={p.precio_regular}
                  precio_promocional={p.precio_promocional}
                  cantidad_maxima_participantes={
                    p.cantidad_maxima_participantes
                  }
                  cantidad_disciplinas_requeridas={
                    p.cantidad_disciplinas_requeridas
                  }
                  disciplinas={p.disciplinas ?? []}
                  isSelected={field.value === p.id}
                  onSelect={() => field.onChange(p.id)}
                />
              ))}
            </div>
          )}
        />
      )}
    </div>
  );
}
