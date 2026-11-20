import type { LucideIcon } from "lucide-react";
import {
  CheckCircle2,
  CircleHelp,
  CircleSlash,
  Clock,
  Loader2,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { RolVeredicto, Veredicto } from "../types/cuenta.types";

/**
 * The visual bucket of every verdict (`SH-01` §3.2).
 *
 * The bucket is PRESENTATIONAL: it says how the chip is painted, never what
 * the verdict means. The meaning lives in the label the backend sent, which
 * the chip prints verbatim.
 *
 * The colour never carries the meaning alone (`SH-02` A11Y-11): every bucket
 * has its own ICON SHAPE and its own TEXT, so a reader who does not see the
 * colour reads the same verdict.
 */
const CUBOS: Record<
  RolVeredicto,
  { icono: LucideIcon; superficie: string; trazo: string }
> = {
  confirmado: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  pendiente: {
    icono: Clock,
    superficie: "border-warning/45 bg-warning/12",
    trazo: "text-warning",
  },
  verificando: {
    icono: Loader2,
    superficie: "border-warning/45 bg-warning/12",
    trazo: "text-warning",
  },
  atencion: {
    icono: TriangleAlert,
    superficie: "border-info/45 bg-info/12",
    trazo: "text-info",
  },
  "sin-confirmar": {
    icono: CircleSlash,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  rechazado: {
    icono: XCircle,
    superficie: "border-destructive/45 bg-destructive/12",
    trazo: "text-destructive",
  },
  desconocido: {
    icono: CircleHelp,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
};

export interface VeredictoEstadoProps {
  /** The verdict: the backend wording plus the visual bucket. */
  veredicto: Veredicto;
  /** Whether the description is shown next to the label. */
  conDescripcion?: boolean;
  className?: string;
}

/**
 * VeredictoEstado - the chip of a verdict.
 *
 * Three things travel together: the SHAPE of the icon, the COLOUR of the
 * bucket and the LABEL of the backend. The label is printed verbatim: the
 * interface never rewrites the wording the server chose (`SH-03` §6).
 *
 * The text keeps the full foreground contrast on purpose: the meaning is
 * read from the words, and the colour is only the redundant signal.
 */
export function VeredictoEstado({
  veredicto,
  conDescripcion = false,
  className,
}: VeredictoEstadoProps) {
  const cubo = CUBOS[veredicto.rol] ?? CUBOS.desconocido;
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
          {veredicto.estado.etiqueta}
        </span>
      </span>
      {conDescripcion ? (
        <span className="text-caption text-muted-foreground">
          {veredicto.estado.descripcion}
        </span>
      ) : null}
    </span>
  );
}
