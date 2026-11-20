import {
  CheckCircle2,
  CircleSlash,
  Clock,
  Loader2,
  TriangleAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { RolPago, VeredictoPago } from "../types/marketplace.types";

/**
 * The visual bucket of every payment verdict (`SH-01` §3.2).
 *
 * The bucket is PRESENTATIONAL: it says how the chip is painted, never what
 * the verdict means. The meaning lives in the label the backend sent, which
 * the chip prints verbatim.
 *
 * The colour never carries the meaning alone (`SH-02` A11Y-11): every bucket
 * has its own ICON SHAPE and its own TEXT.
 */
const CUBOS: Record<
  RolPago,
  { icono: LucideIcon; superficie: string; trazo: string }
> = {
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
 * The safe next step of each of the five presentable payment states.
 *
 * `SH-03` §3 and `frontend/03` ("Componente compartido de pago") fix the CTA
 * of every state. The label of the VERDICT comes from the backend; the CTA is
 * the affordance of this surface and never repeats an operation that already
 * ran (`S-09`: a safe follow-up).
 */
const ACCIONES: Record<RolPago, string> = {
  pendiente: "Continuar pago",
  verificando: "Consultar más tarde",
  confirmado: "Ver entradas",
  "sin-confirmar": "Reintentar de forma segura",
  atencion: "Contactar soporte",
};

export interface EstadoPagoTiendaProps {
  /** The verdict: the backend wording plus the visual bucket. */
  veredicto: VeredictoPago;
  /** Whether the explanation of the backend is shown next to the label. */
  conDescripcion?: boolean;
  /**
   * The next step.
   *
   * When it is absent the state is shown WITHOUT a call to action: a button
   * that cannot do anything is a dead end (`SH-03` §2).
   */
  accion?: {
    /** Overrides the default CTA of the state. */
    etiqueta?: string;
    href?: string;
    onClick?: () => void;
  };
  className?: string;
}

/**
 * EstadoPagoTienda - the chip of a payment verdict.
 *
 * Three things travel together: the SHAPE of the icon, the COLOUR of the
 * bucket and the LABEL of the backend. The label is printed verbatim: the
 * interface never rewrites the wording the server chose (`SH-03` §6).
 *
 * The client never derives a payment state from a modal close or a timeout
 * (`GOV-02-RB-02d`): it draws the verdict it is given.
 */
export function EstadoPagoTienda({
  veredicto,
  conDescripcion = false,
  accion,
  className,
}: EstadoPagoTiendaProps) {
  const cubo = CUBOS[veredicto.rol] ?? CUBOS["sin-confirmar"];
  const Icono = cubo.icono;
  const etiquetaAccion = accion?.etiqueta ?? ACCIONES[veredicto.rol];

  return (
    <span className={cn("inline-flex flex-col gap-1.5", className)}>
      <span
        className={cn(
          "inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1",
          cubo.superficie,
        )}
      >
        <Icono className={cn("size-3.5 shrink-0", cubo.trazo)} aria-hidden="true" />
        <span className="text-xs font-semibold text-foreground">
          {veredicto.estado.etiqueta}
        </span>
      </span>

      {conDescripcion ? (
        <span className="text-caption text-muted-foreground">
          {veredicto.estado.descripcion}
        </span>
      ) : null}

      {accion ? (
        accion.href ? (
          <Button asChild variant="outline" size="sm" className="min-h-11 w-fit">
            <Link href={accion.href}>{etiquetaAccion}</Link>
          </Button>
        ) : (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11 w-fit"
            onClick={accion.onClick}
          >
            {etiquetaAccion}
          </Button>
        )
      ) : null}
    </span>
  );
}
