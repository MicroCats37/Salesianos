import {
  Ban,
  CheckCircle2,
  CircleHelp,
  CircleSlash,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  RolVeredictoValidacion,
  VeredictoValidacion,
} from "../types/validacion.types";

/**
 * The bucket of every verdict of the area (`SH-01` §3.2).
 *
 * The bucket is PRESENTATIONAL: it says how the chip is painted, never what
 * the verdict means. The meaning lives in the label the backend published and
 * the chip prints it VERBATIM (`SH-03` §6).
 *
 * The colour never carries the meaning alone (`SH-02` A11Y-11): every bucket
 * has its own ICON SHAPE, so a reader who does not see the colour reads the
 * same verdict.
 */
const CUBOS: Record<
  RolVeredictoValidacion,
  { icono: LucideIcon; superficie: string; trazo: string }
> = {
  permitido: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  denegado: {
    icono: XCircle,
    superficie: "border-destructive/45 bg-destructive/12",
    trazo: "text-destructive",
  },
  parcial: {
    icono: TriangleAlert,
    superficie: "border-warning/45 bg-warning/12",
    trazo: "text-warning",
  },
  consumido: {
    icono: CircleSlash,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  revocado: {
    icono: Ban,
    superficie: "border-destructive/45 bg-destructive/12",
    trazo: "text-destructive",
  },
  excedido: {
    icono: TriangleAlert,
    superficie: "border-warning/45 bg-warning/12",
    trazo: "text-warning",
  },
  desconocido: {
    icono: CircleHelp,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
};

export interface ChipVeredictoValidacionProps {
  /** The verdict: the wording of the backend plus the bucket that paints it. */
  veredicto: VeredictoValidacion;
  /** Whether the reason is shown next to the label. */
  conDescripcion?: boolean;
  className?: string;
}

/**
 * ChipVeredictoValidacion - the chip of a verdict of the area.
 *
 * Three things travel together: the SHAPE of the icon, the COLOUR of the
 * bucket and the LABEL of the backend. The text keeps the full foreground
 * contrast on purpose: the meaning is read from the words and the colour is
 * only the redundant signal.
 */
export function ChipVeredictoValidacion({
  veredicto,
  conDescripcion = false,
  className,
}: ChipVeredictoValidacionProps) {
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
          {veredicto.estado.codigo}
        </span>
      ) : null}
    </span>
  );
}
