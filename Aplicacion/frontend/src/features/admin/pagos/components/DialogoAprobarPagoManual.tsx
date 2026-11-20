"use client";

import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { ConfirmacionIrreversible } from "@/features/admin/operaciones";
import {
  erroresDeCampoDeError,
  mensajeDeError,
} from "@/features/admin/operaciones/utils/admin.estado.utils";
import { useAprobarPagoManualAdmin } from "../hooks/usePagosAdmin";

export interface DialogoAprobarPagoManualProps {
  /** Whether the confirmation is open. */
  abierto: boolean;
  /** Called when the confirmation opens or closes. */
  onAbiertoChange: (abierto: boolean) => void;
  /** The concept of the purchase, as the presenter published it. */
  concepto: string;
  /** The amount of the purchase, as the server sends it. */
  monto: string;
  /** The currency of the purchase. */
  moneda: string;
  /** The payment order that the command confirms. */
  ordenPagoId?: string;
}

/**
 * DialogoAprobarPagoManual - the S-10 state of the manual approval.
 *
 * `GOV-02-RB-06`: the manual approval is NOT a ubiquitous button. It is a
 * contextual action that the presenter projects for a concrete purchase, and
 * its confirmation names the EFFECT and captures the audited reason.
 *
 * ## The action is DISABLED, and the reason is the TRUTH of the backend
 *
 * `RT-PG-05` (`POST /administracion/pagos/{orden_pago_id}/aprobar-manual`) is
 * FROZEN in GOV-01 but its controller is NOT registered in the backend, so
 * the route DOES NOT EXIST. The button is disabled from the SAME registry that
 * the service uses (`RUTAS_ADMIN.aprobarPagoManual.registrado`).
 *
 * ## The amount is never calculated
 *
 * The command sends the amount that the SERVER published: the browser does
 * not compute a price and does not send one it invented (`FR-08` §2.4).
 */
export function DialogoAprobarPagoManual({
  abierto,
  onAbiertoChange,
  concepto,
  monto,
  moneda,
  ordenPagoId,
}: DialogoAprobarPagoManualProps) {
  const aprobar = useAprobarPagoManualAdmin();

  const conectado = RUTAS_ADMIN.aprobarPagoManual.registrado;
  const listo = conectado && Boolean(ordenPagoId);
  const mensaje = aprobar.error ? mensajeDeError(aprobar.error) : undefined;
  const errorDeCampo = aprobar.error
    ? erroresDeCampoDeError(aprobar.error).motivo
    : undefined;

  return (
    <ConfirmacionIrreversible
      abierto={abierto}
      onAbiertoChange={onAbiertoChange}
      titulo="Registrar el pago externo"
      efecto={`Registrar ${monto} ${moneda} de «${concepto}» habilita los derechos de esta compra y queda registrado en la auditoría con el motivo indicado.`}
      motivo={{
        etiqueta: "Motivo del registro",
        placeholder:
          "Escribe el motivo y la referencia del pago que quedan registrados.",
        requerido: true,
      }}
      confirmar={{
        etiqueta: "Registrar el pago",
        deshabilitado: !listo,
        enCurso: aprobar.isPending,
      }}
      error={mensaje}
      errorDeCampo={errorDeCampo}
      onConfirmar={(motivo) => {
        if (!ordenPagoId) return;

        aprobar.mutate({
          orden_pago_id: ordenPagoId,
          monto,
          moneda,
          motivo,
        });
      }}
    />
  );
}
