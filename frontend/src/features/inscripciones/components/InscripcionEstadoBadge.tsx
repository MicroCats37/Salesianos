"use client";

import {
  AlertCircle,
  CheckCircle2,
  Clock4,
  PartyPopper,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type InscripcionEstadoSize = "sm" | "lg";

interface EstadoMeta {
  /** Human label of the administrative state. */
  label: string;
  /** What the state means for the responsable. */
  description: string;
  /** Pill surface + text. */
  pillClass: string;
  icon: React.ComponentType<{ className?: string }>;
}

/**
 * Administrative states of an inscription.
 *
 * The state is ADMINISTRATIVE: it never describes the commercial state. The
 * payment is decided by `resumen_pago` (see `utils/pago.estado.ts`).
 */
export const ESTADO_INSCRIPCION_META: Record<string, EstadoMeta> = {
  BORRADOR: {
    label: "Borrador",
    description:
      "Inscripcion creada. Revisa el paquete y la promocion antes de enviarla al Comite.",
    pillClass: "bg-amber-500/10 text-amber-700 border-amber-200",
    icon: Clock4,
  },
  RECIBIDA: {
    label: "Recibida",
    description:
      "Recibimos tu inscripcion. Esta en cola de revision del Comite Organizador.",
    pillClass: "bg-blue-500/10 text-blue-700 border-blue-200",
    icon: ShieldCheck,
  },
  EN_REVISION: {
    label: "En revisión",
    description: "El Comite Organizador esta revisando tu inscripcion.",
    pillClass: "bg-violet-500/10 text-violet-700 border-violet-200",
    icon: ShieldCheck,
  },
  OBSERVADA: {
    label: "Observada",
    description:
      "El Comite Organizador requiere ajustes. Revisa la observacion del resumen.",
    pillClass: "bg-orange-500/10 text-orange-700 border-orange-200",
    icon: AlertCircle,
  },
  VALIDADA: {
    label: "Validada",
    description:
      "Inscripcion validada. Completa el pago para que los cupos queden activos.",
    pillClass: "bg-cyan-500/10 text-cyan-700 border-cyan-200",
    icon: CheckCircle2,
  },
  CONFIRMADA: {
    label: "Confirmada",
    description: "Pago confirmado. El equipo ya queda inscrito en el festival.",
    pillClass: "bg-emerald-500/10 text-emerald-700 border-emerald-200",
    icon: PartyPopper,
  },
  RECHAZADA: {
    label: "Rechazada",
    description:
      "Inscripcion rechazada. Contacta al Comite Organizador para conocer el motivo.",
    pillClass: "bg-red-500/10 text-red-700 border-red-200",
    icon: XCircle,
  },
  CANCELADA: {
    label: "Cancelada",
    description:
      "Inscripcion cancelada. Contacta al Comite Organizador para mas detalles.",
    pillClass: "bg-rose-500/10 text-rose-700 border-rose-200",
    icon: XCircle,
  },
};

const ESTADO_FALLBACK: EstadoMeta = {
  label: "Sin estado",
  description:
    "El Comite Organizador todavia no reviso esta inscripcion. Puedes seguir avanzando con los participantes.",
  pillClass: "bg-slate-500/10 text-slate-700 border-slate-200",
  icon: ShieldCheck,
};

/** Metadata of an administrative state, with a safe fallback. */
export function estadoInscripcionMeta(estado: string): EstadoMeta {
  return (
    ESTADO_INSCRIPCION_META[estado] ?? {
      ...ESTADO_FALLBACK,
      label: estado || ESTADO_FALLBACK.label,
    }
  );
}

interface InscripcionEstadoBadgeProps {
  estado: string;
  size?: InscripcionEstadoSize;
  className?: string;
}

/**
 * Badge of the administrative state of an inscription.
 *
 * It is the same visual language used by the dashboard cards, so the user
 * recognises the state at a glance on both screens.
 */
export function InscripcionEstadoBadge({
  estado,
  size = "sm",
  className,
}: InscripcionEstadoBadgeProps) {
  const meta = estadoInscripcionMeta(estado);

  return (
    <span
      data-size={size}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-wider",
        meta.pillClass,
        className,
      )}
    >
      {meta.label}
    </span>
  );
}
