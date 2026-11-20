import type { LucideIcon } from "lucide-react";
import {
  Ban,
  CheckCircle2,
  CircleDot,
  Clock,
  Pencil,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EstadoConRol, RolEstado } from "../types/competencia.types";

/**
 * The bucket of every state of the area (`SH-01` §3.2).
 *
 * The bucket is PRESENTATIONAL: it says how the chip is painted, never what
 * the state means. The meaning lives in the label the backend published, and
 * the chip prints that label VERBATIM (`SH-03` §6).
 *
 * The colour never carries the meaning alone (`SH-02` A11Y-11): every bucket
 * has its own ICON SHAPE, so a reader who does not see the colour reads the
 * same state.
 */
const CUBOS: Record<
  RolEstado,
  { icono: LucideIcon; superficie: string; trazo: string }
> = {
  "en-curso": {
    icono: CircleDot,
    superficie: "border-info/45 bg-info/12",
    trazo: "text-info",
  },
  planificado: {
    icono: Clock,
    superficie: "border-warning/45 bg-warning/12",
    trazo: "text-warning",
  },
  finalizado: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  borrador: {
    icono: Pencil,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  cancelado: {
    icono: Ban,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  activo: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  retirado: {
    icono: Ban,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  elegible: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  bloqueado: {
    icono: XCircle,
    superficie: "border-destructive/45 bg-destructive/12",
    trazo: "text-destructive",
  },
};

export interface ChipEstadoCompetenciaProps {
  /** The state and the bucket that paints it. */
  estado: EstadoConRol;
  /** The extra explanation, under the label. */
  descripcion?: string;
  className?: string;
}

/**
 * ChipEstadoCompetencia - the chip of a state of the competitions area.
 *
 * Three things travel together: the SHAPE of the icon, the COLOUR of the
 * bucket and the LABEL of the backend. The text keeps the full foreground
 * contrast on purpose: the meaning is read from the words and the colour is
 * only the redundant signal.
 */
export function ChipEstadoCompetencia({
  estado,
  descripcion,
  className,
}: ChipEstadoCompetenciaProps) {
  const cubo = CUBOS[estado.rol] ?? CUBOS.bloqueado;
  const Icono = cubo.icono;

  return (
    <span className={cn("inline-flex flex-col gap-0.5", className)}>
      <span
        className={cn(
          "inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1",
          cubo.superficie,
        )}
      >
        <Icono
          className={cn("size-3.5 shrink-0", cubo.trazo)}
          aria-hidden="true"
        />
        <span className="text-xs font-semibold text-foreground">
          {estado.estado.etiqueta}
        </span>
      </span>
      {descripcion ? (
        <span className="text-caption text-muted-foreground">
          {descripcion}
        </span>
      ) : null}
    </span>
  );
}

/**
 * The chip of a state that the backend refused to explain.
 *
 * It exists for the case where the operation is BLOCKED and the reason is not
 * a state but an event: the icon changes and the reason travels with it.
 */
export function ChipBloqueo({
  motivo,
  className,
}: {
  motivo: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center gap-1.5 rounded-full border border-destructive/45 bg-destructive/12 px-2.5 py-1",
        className,
      )}
    >
      <TriangleAlert
        className="size-3.5 shrink-0 text-destructive"
        aria-hidden="true"
      />
      <span className="text-xs font-semibold text-foreground">{motivo}</span>
    </span>
  );
}
