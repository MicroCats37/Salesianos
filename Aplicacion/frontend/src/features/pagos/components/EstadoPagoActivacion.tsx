import type { VeredictoActivacion } from "../types/pagos.types";
import { CUBOS_ACTIVACION } from "./buckets.pago";
import { ChipPago } from "./ChipPago";

export interface EstadoPagoActivacionProps {
  /** The verdict of the activation, with the bucket the adapter resolved. */
  veredicto: VeredictoActivacion;
  /** Whether the explanation of the backend is shown next to the label. */
  conDescripcion?: boolean;
  className?: string;
}

/**
 * EstadoPagoActivacion - the chip of the ACTIVATION channel.
 *
 * The activation verdict answers "is the right enabled?", which is a
 * DIFFERENT question from the operator verdict "is it paid?" (`RN-C07` ·
 * `contratos/01` §1.4). The two channels therefore never share a chip: mixing
 * them would let a screen say "paid" where the backend said "activated", or
 * the other way round.
 *
 * The label printed is the one the backend sent, verbatim, and the machine
 * code never reaches the screen (`SH-03` §6).
 *
 * There is NO call to action: the activation verdict publishes the next step
 * as WORDS (`proxima_accion`), and a button that cannot do anything is a
 * dead end (`SH-03` §2). The surface that owns the action decides what to do
 * with it.
 */
export function EstadoPagoActivacion({
  veredicto,
  conDescripcion = false,
  className,
}: EstadoPagoActivacionProps) {
  const cubo = CUBOS_ACTIVACION[veredicto.rol] ?? CUBOS_ACTIVACION.desconocido;

  return (
    <ChipPago
      etiqueta={veredicto.estado.etiqueta}
      descripcion={conDescripcion ? veredicto.estado.descripcion : undefined}
      icono={cubo.icono}
      superficie={cubo.superficie}
      trazo={cubo.trazo}
      className={className}
    />
  );
}
