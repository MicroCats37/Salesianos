"use client";

import { gsap } from "gsap";
import {
  FileText,
  Heart,
  ImageIcon,
  Package,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useRef } from "react";
import { useFormContext } from "react-hook-form";
import { usePaquetes } from "../../hooks/useInscripcionCatalogs";
import type { InscripcionFormData } from "../../schemas/inscripcion.schema";

// ── Consents Shape (local wizard state) ───────────────────────────────────────

export interface WizardConsents {
  bases: boolean;
  aptitudFisica: boolean;
  imagen: boolean;
}

// ── Summary Item ─────────────────────────────────────────────────────────────

interface SummaryItemProps {
  label: string;
  value: string | undefined;
  highlight?: boolean;
  large?: boolean;
}

function SummaryItem({ label, value, highlight, large }: SummaryItemProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2 last:border-b-0">
      <span
        className={
          large
            ? "text-sm font-bold uppercase tracking-wider text-slate-700"
            : "text-sm font-medium text-slate-500"
        }
      >
        {label}
      </span>
      <span
        className={
          large
            ? "text-2xl font-black text-emerald-700"
            : highlight
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

interface StepDeclarationsProps {
  /** Local wizard state — consents are NOT in the form schema. */
  consents: WizardConsents;
  setConsents: React.Dispatch<React.SetStateAction<WizardConsents>>;
}

export function StepDeclarations({
  consents,
  setConsents,
}: StepDeclarationsProps) {
  const { watch } = useFormContext<InscripcionFormData>();

  const selectedPaqueteId = watch("paquete_id");
  const equipos = watch("equipos") ?? [];
  // Cantidad y precio cotizado seleccionados en step 1 (persistidos en el form).
  const cantidadSeleccionada = watch("cantidad");
  const precioUnitarioCotizado = watch("precio_unitario_cotizado");

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

  // Precio unitario de referencia: el cotizado (si lo hay) o el del catálogo.
  // Se usa SOLO para mostrar la referencia "X c/u" en el total — no es el dato
  // principal del step 3.
  const precioUnitarioRef =
    precioUnitarioCotizado ??
    selectedPaquete?.precio_preventa ??
    selectedPaquete?.precio_regular ??
    0;

  // Total que el usuario va a pagar (snapshot de lo que se enviará al backend).
  // Si hay cotización persistida, ese es el dato autoritativo; si no, se
  // calcula localmente con la cantidad del form y el precio del catálogo.
  const cantidadFinal = cantidadSeleccionada ?? 0;
  const totalFinal = precioUnitarioCotizado
    ? precioUnitarioCotizado * cantidadFinal
    : precioUnitarioRef * cantidadFinal;

  const setConsent = (key: keyof WizardConsents, val: boolean) =>
    setConsents((prev) => ({ ...prev, [key]: val }));

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
            label="Participantes agregados"
            value={`${totalParticipantes} jugador${totalParticipantes !== 1 ? "es" : ""}`}
          />
          <SummaryItem
            label="Cantidad"
            value={
              cantidadFinal > 0
                ? `${cantidadFinal} jugador${cantidadFinal !== 1 ? "es" : ""}`
                : "—"
            }
          />
          {/* Total a pagar — el dato PRINCIPAL del resumen, no el unitario. */}
          <SummaryItem
            label="Total a pagar"
            value={
              cantidadFinal > 0
                ? `S/${totalFinal.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : "—"
            }
            large
          />
          {/* Precio unitario (referencia secundaria) */}
          {cantidadFinal > 0 && precioUnitarioRef > 0 && (
            <SummaryItem
              label="Precio por persona"
              value={`S/${precioUnitarioRef.toFixed(2)}`}
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
          <DeclarationCheckbox
            id="acceptedBases"
            label="Acepto las bases del evento"
            description="He leído y acepto las bases oficiales del evento Salesianos FEST 2026."
            icon={FileText}
            checked={consents.bases}
            onChange={(val) => setConsent("bases", val)}
          />
        </div>

        <div className="declaration-item">
          <DeclarationCheckbox
            id="fitnessDeclaration"
            label="Declaro estar apta/o físicamente"
            description="Declaro que me encuentro en condiciones físicas adecuadas para participar en las disciplinas seleccionadas."
            icon={Heart}
            checked={consents.aptitudFisica}
            onChange={(val) => setConsent("aptitudFisica", val)}
          />
        </div>

        <div className="declaration-item">
          <DeclarationCheckbox
            id="imageConsent"
            label="Autorizo el uso de mi imagen"
            description="Autorizo a los organizadores a utilizar fotografías y videos de mi participación para fines promocionales."
            icon={ImageIcon}
            checked={consents.imagen}
            onChange={(val) => setConsent("imagen", val)}
          />
        </div>
      </div>
    </div>
  );
}
