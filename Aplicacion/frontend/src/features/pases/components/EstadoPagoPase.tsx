import { ChipPago, CUBOS_PAGO } from "@/features/pagos/components";
import type { RolPago, VeredictoPago } from "../types/pase.types";

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

export interface EstadoPagoPaseProps {
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
 * EstadoPagoPase - the chip of a payment verdict.
 *
 * Three things travel together: the SHAPE of the icon, the COLOUR of the
 * bucket and the LABEL of the backend. The label is printed verbatim: the
 * interface never rewrites the wording the server chose (`SH-03` §6).
 *
 * The PAINT is not owned here. The buckets of the payment channel live in the
 * payment area (`features/pagos/components`), because the visual payment
 * component is shared by every checkout of the product (`GOV-02-RB-02a`). What
 * belongs to this surface is the NEXT STEP of each state: the pass surface is
 * the one that knows which action makes sense for a pass.
 *
 * The client never derives a payment state from a modal close or a timeout
 * (`GOV-02-RB-02d`): it draws the verdict it is given.
 */
export function EstadoPagoPase({
  veredicto,
  conDescripcion = false,
  accion,
  className,
}: EstadoPagoPaseProps) {
  const cubo = CUBOS_PAGO[veredicto.rol] ?? CUBOS_PAGO["sin-confirmar"];
  const etiquetaAccion = accion?.etiqueta ?? ACCIONES[veredicto.rol];

  return (
    <ChipPago
      etiqueta={veredicto.estado.etiqueta}
      descripcion={conDescripcion ? veredicto.estado.descripcion : undefined}
      icono={cubo.icono}
      superficie={cubo.superficie}
      trazo={cubo.trazo}
      accion={accion ? { ...accion, etiqueta: etiquetaAccion } : undefined}
      className={className}
    />
  );
}
