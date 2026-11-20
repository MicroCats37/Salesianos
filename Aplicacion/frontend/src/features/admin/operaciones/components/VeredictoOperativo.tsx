import type { LucideIcon } from "lucide-react";
import {
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CircleX,
  Clock,
  MinusCircle,
  TriangleAlert,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { RolOperativo, Veredicto } from "../types/operaciones.types";

/**
 * The shape of a bucket: the icon that gives it a SILHOUETTE and the semantic
 * roles it paints with.
 *
 * The colour never carries the meaning alone (`SH-01` §3.2): every chip pairs
 * an icon, the label of the backend and a semantic surface. Only the LABEL is
 * read by a screen reader as text.
 */
const ROL_ESTILO: Record<
  RolOperativo,
  { Icono: LucideIcon; clase: string; claseIcono: string }
> = {
  confirmado: {
    Icono: CircleCheck,
    clase: "border-success/30 bg-success/10",
    claseIcono: "text-success",
  },
  pendiente: {
    Icono: Clock,
    clase: "border-warning/30 bg-warning/10",
    claseIcono: "text-warning",
  },
  atencion: {
    Icono: CircleAlert,
    clase: "border-info/30 bg-info/10",
    claseIcono: "text-info",
  },
  "sin-confirmar": {
    Icono: MinusCircle,
    clase: "border-border bg-muted/50",
    claseIcono: "text-foreground-muted",
  },
  incompleto: {
    Icono: TriangleAlert,
    clase: "border-warning/30 bg-warning/10",
    claseIcono: "text-warning",
  },
  rechazado: {
    Icono: CircleX,
    clase: "border-destructive/30 bg-destructive/10",
    claseIcono: "text-destructive",
  },
  desconocido: {
    Icono: CircleHelp,
    clase: "border-border bg-muted/50",
    claseIcono: "text-foreground-muted",
  },
};

export interface VeredictoOperativoProps {
  /** The verdict of the backend, with its visual bucket. */
  veredicto: Veredicto;
  /** Extra classes of the chip. */
  className?: string;
}

/**
 * VeredictoOperativo - the chip of an operational verdict.
 *
 * It shows THREE things and never a fourth: the SILHOUETTE of the bucket
 * (the icon), the LABEL of the backend and the semantic surface. It never
 * shows the machine code (`SH-03` §6) and it never derives the verdict from
 * the raw fields of a purchase, of an order or of an attempt
 * (`GOV-02-RB-06a`).
 */
export function VeredictoOperativo({
  veredicto,
  className,
}: VeredictoOperativoProps) {
  const estilo = ROL_ESTILO[veredicto.rol] ?? ROL_ESTILO.desconocido;
  const Icono = estilo.Icono;

  return (
    <span
      data-operacion="veredicto"
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs leading-tight font-semibold text-foreground",
        estilo.clase,
        className,
      )}
    >
      <Icono
        className={cn("size-3.5 shrink-0", estilo.claseIcono)}
        aria-hidden="true"
      />
      <span className="min-w-0 truncate">{veredicto.estado.etiqueta}</span>
    </span>
  );
}

export interface VeredictoConCausaProps {
  /** The verdict of the backend, with its visual bucket. */
  veredicto: Veredicto;
  className?: string;
}

/**
 * VeredictoConCausa - the chip of a verdict WITH its cause.
 *
 * `GOV-02-RB-04`: the list of teams has to say WHY a team cannot compete.
 * The cause is the `descripcion` of the backend, printed underneath the
 * chip, so the row reads as a sentence and never as a coloured dot.
 */
export function VeredictoConCausa({
  veredicto,
  className,
}: VeredictoConCausaProps) {
  return (
    <div
      data-operacion="veredicto-con-causa"
      className={cn("flex flex-col gap-1", className)}
    >
      <VeredictoOperativo veredicto={veredicto} />
      <p className="max-w-prose text-xs leading-snug text-muted-foreground">
        {veredicto.estado.descripcion}
      </p>
    </div>
  );
}

export interface ExplicacionVeredictoProps {
  /** The verdict of the backend, with its visual bucket. */
  veredicto: Veredicto;
  /** The next permitted action, as the presenter named it. */
  siguienteAccion?: ReactNode;
  className?: string;
}

/**
 * ExplicacionVeredicto - the REASON of a verdict and its next step.
 *
 * This is the piece that makes an operational surface usable: the operator
 * reads the cause, not a coloured dot, and the next step is the one the
 * backend named. `GOV-02-RB-04b`: every "why" of these pages is the backend's
 * `estado_operativo.etiqueta` plus its `descripcion`.
 */
export function ExplicacionVeredicto({
  veredicto,
  siguienteAccion,
  className,
}: ExplicacionVeredictoProps) {
  return (
    <div
      data-operacion="explicacion"
      className={cn("flex flex-col gap-2", className)}
    >
      <VeredictoOperativo veredicto={veredicto} />
      <p className="max-w-measure text-sm leading-relaxed text-muted-foreground">
        {veredicto.estado.descripcion}
      </p>
      {siguienteAccion ? (
        <div className="flex min-h-11 flex-wrap items-center gap-2">
          {siguienteAccion}
        </div>
      ) : null}
    </div>
  );
}
