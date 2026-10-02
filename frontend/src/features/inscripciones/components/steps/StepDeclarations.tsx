"use client";

import { gsap } from "gsap";
import { FileText, Heart, ImageIcon, Package, ShieldCheck, Users } from "lucide-react";
import { useEffect, useRef } from "react";
import { Controller, useFormContext } from "react-hook-form";
import { usePaquetes } from "../../hooks/useInscripcionCatalogs";
import type { InscripcionFormData } from "../../schemas/inscripcion.schema";

// ── Summary Item ─────────────────────────────────────────────────────────────

interface SummaryItemProps {
  label: string;
  value: string | undefined;
  highlight?: boolean;
}

function SummaryItem({ label, value, highlight }: SummaryItemProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2 last:border-b-0">
      <span className="text-sm font-medium text-slate-500">{label}</span>
      <span
        className={
          highlight
            ? "text-sm font-bold text-amber-700"
            : "text-sm font-semibold text-slate-900"
        }
      >
        {value ?? "—"}
      </span>
    </div>
  );
}

// ── Declaration Checkbox ─────────────────────────────────────────────────────

interface DeclarationCheckboxProps {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  checked: boolean;
  onChange: (val: boolean) => void;
  error?: string;
}

function DeclarationCheckbox({
  id,
  label,
  description,
  icon: Icon,
  checked,
  onChange,
  error,
}: DeclarationCheckboxProps) {
  return (
    <label
      htmlFor={id}
      className={`flex cursor-pointer items-start gap-3 rounded-xl border bg-white p-4 shadow-sm transition-all ${
        checked
          ? "border-emerald-300 ring-2 ring-emerald-100"
          : error
            ? "border-red-300"
            : "border-slate-200 hover:border-emerald-300"
      }`}
    >
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="peer sr-only"
      />
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors ${
          checked
            ? "bg-gradient-to-br from-emerald-400 to-emerald-600 text-white"
            : "bg-slate-100 text-slate-500"
        }`}
      >
        <Icon className="size-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-slate-900">{label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{description}</p>
      </div>
      <div
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
          checked
            ? "border-emerald-500 bg-emerald-500"
            : "border-slate-300 bg-white"
        }`}
      >
        {checked && (
          <svg
            viewBox="0 0 12 12"
            className="h-3 w-3 text-white"
            fill="currentColor"
            aria-hidden="true"
          >
            <title>Checked</title>
            <path d="M10.28 2.28L3.989 8.575 1.695 6.28A1 1 0 00.281 7.695l3 3a1 1 0 001.414 0l7-7A1 1 0 0010.28 2.28z" />
          </svg>
        )}
      </div>
    </label>
  );
}

// ── Step Component ─────────────────────────────────────────────────────────────

export function StepDeclarations() {
  const { control, watch } = useFormContext<InscripcionFormData>();

  const selectedPaqueteId = watch("paquete_id");
  const equipos = watch("equipos") ?? [];

  const { data: paquetes } = usePaquetes();

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".declaration-item",
        { y: 20, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: "power3.out",
        },
      );
    }, container);
    return () => ctx.revert();
  }, []);

  const selectedPaquete = paquetes?.find((p) => p.id === selectedPaqueteId);
  const totalParticipantes = equipos.reduce(
    (acc, eq) =>
      acc + ((eq as { participantes?: unknown[] }).participantes?.length ?? 0),
    0,
  );

  return (
    <div ref={containerRef} className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
          <ShieldCheck className="size-5" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">
            Declaraciones y Resumen
          </h3>
          <p className="text-sm text-slate-500">
            Revisa la información y acepta las declaraciones antes de enviar.
          </p>
        </div>
      </div>

      {/* Summary Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 text-white">
            <Package className="size-4" />
          </div>
          <h4 className="text-sm font-bold uppercase tracking-wider text-amber-700">
            Resumen de inscripción
          </h4>
        </div>
        <div className="space-y-0">
          <SummaryItem
            label="Paquete"
            value={selectedPaquete?.nombre}
            highlight
          />
          <SummaryItem
            label="Equipos"
            value={`${equipos.length} equipo${equipos.length !== 1 ? "s" : ""}`}
          />
          <SummaryItem
            label="Participantes"
            value={`${totalParticipantes} jugador${totalParticipantes !== 1 ? "es" : ""}`}
          />
          {selectedPaquete?.precio_promocional && (
            <SummaryItem
              label="Precio"
              value={`S/${selectedPaquete.precio_promocional.toFixed(2)}`}
              highlight
            />
          )}
          {selectedPaquete && !selectedPaquete.precio_promocional && (
            <SummaryItem
              label="Precio"
              value={`S/${selectedPaquete.precio_regular.toFixed(2)}`}
              highlight
            />
          )}
        </div>
      </div>

      {/* Declarations */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 text-white">
            <Users className="size-4" />
          </div>
          <h4 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Declaraciones requeridas
          </h4>
        </div>

        <div className="declaration-item">
          <Controller
            name="acceptedBases"
            control={control}
            render={({ field }) => (
              <DeclarationCheckbox
                id="acceptedBases"
                label="Acepto las bases del evento"
                description="He leído y acepto las bases oficiales del evento Salesianos FEST 2026."
                icon={FileText}
                checked={field.value === true}
                onChange={(val) => field.onChange(!!val)}
                error={undefined}
              />
            )}
          />
        </div>

        <div className="declaration-item">
          <Controller
            name="fitnessDeclaration"
            control={control}
            render={({ field }) => (
              <DeclarationCheckbox
                id="fitnessDeclaration"
                label="Declaro estar apta/o físicamente"
                description="Declaro que me encuentro en condiciones físicas adecuadas para participar en las disciplinas seleccionadas."
                icon={Heart}
                checked={field.value === true}
                onChange={(val) => field.onChange(!!val)}
                error={undefined}
              />
            )}
          />
        </div>

        <div className="declaration-item">
          <Controller
            name="imageConsent"
            control={control}
            render={({ field }) => (
              <DeclarationCheckbox
                id="imageConsent"
                label="Autorizo el uso de mi imagen"
                description="Autorizo a los organizadores a utilizar fotografías y videos de mi participación para fines promocionales."
                icon={ImageIcon}
                checked={field.value === true}
                onChange={(val) => field.onChange(!!val)}
                error={undefined}
              />
            )}
          />
        </div>
      </div>
    </div>
  );
}
