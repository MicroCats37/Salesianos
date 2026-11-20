import type { LucideIcon } from "lucide-react";
import {
  CheckCircle2,
  CircleSlash,
  CircleX,
  Clock,
  Loader2,
  TriangleAlert,
} from "lucide-react";

/**
 * The vocabulary of PAINT of the payment area.
 *
 * A bucket says HOW a verdict is painted, never WHAT it means. The wording
 * and the meaning always come from the backend, and the colour never carries
 * the meaning alone: every bucket has its own ICON SHAPE and its own TEXT
 * (`SH-01` §3.2).
 *
 * The map is PRESENTATIONAL. A component NEVER branches on a business code:
 * the catalogue of public codes is not closed, and a component that decided
 * what a code means would break with the next code the backend catalogues
 * (`SH-03` §6).
 */
export interface CuboPago {
  /** The shape of the icon that accompanies the colour. */
  icono: LucideIcon;
  /** The classes of the surface of the chip. */
  superficie: string;
  /** The classes of the stroke of the icon. */
  trazo: string;
}

/**
 * The five presentable payment states of `SH-03` §3.
 *
 * They are the states of the OPERATOR channel — "is it paid?" — and they are
 * shared by every checkout of the product (`GOV-02-RB-02a`).
 */
export type RolPagoCompartido =
  | "pendiente"
  | "verificando"
  | "confirmado"
  | "sin-confirmar"
  | "atencion";

/**
 * The buckets of the five presentable payment states.
 *
 * The values are the ones the pass surface already painted: moving the map
 * here does not change a single colour of a single verdict, it only gives
 * the map ONE owner that every checkout can share.
 */
export const CUBOS_PAGO: Record<RolPagoCompartido, CuboPago> = {
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
  confirmado: {
    icono: CheckCircle2,
    superficie: "border-success/45 bg-success/12",
    trazo: "text-success",
  },
  "sin-confirmar": {
    icono: CircleSlash,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
  atencion: {
    icono: TriangleAlert,
    superficie: "border-info/45 bg-info/12",
    trazo: "text-info",
  },
};

/**
 * The buckets of the ACTIVATION channel.
 *
 * The activation verdict is a channel SEPARATE from the operator verdict: it
 * answers "is the right enabled?" and not "is it paid?" (`RN-C07` ·
 * `contratos/01` §1.4). It therefore has its own map, with the two buckets
 * that only the activation channel knows.
 */
export type RolActivacionVisual =
  | RolPagoCompartido
  | "rechazado"
  | "desconocido";

export const CUBOS_ACTIVACION: Record<RolActivacionVisual, CuboPago> = {
  ...CUBOS_PAGO,
  rechazado: {
    icono: CircleX,
    superficie: "border-destructive/45 bg-destructive/12",
    trazo: "text-destructive",
  },
  desconocido: {
    icono: CircleSlash,
    superficie: "border-border bg-surface-recessed",
    trazo: "text-foreground-muted",
  },
};
