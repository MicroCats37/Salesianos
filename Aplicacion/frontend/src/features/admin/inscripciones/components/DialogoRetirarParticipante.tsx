"use client";

import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { ConfirmacionIrreversible } from "@/features/admin/operaciones";
import {
  erroresDeCampoDeError,
  mensajeDeError,
} from "@/features/admin/operaciones/utils/admin.estado.utils";
import { useRetirarParticipanteAdmin } from "../hooks/useInscripcionesAdmin";

export interface DialogoRetirarParticipanteProps {
  /** Whether the confirmation is open. */
  abierto: boolean;
  /** Called when the confirmation opens or closes. */
  onAbiertoChange: (abierto: boolean) => void;
  /** The name of the participant that would be withdrawn. */
  nombreParticipante: string;
  /** The registration that owns the participation. */
  inscripcionId?: string;
  /** The participation that would be withdrawn. */
  participacionId?: string;
}

/**
 * DialogoRetirarParticipante - the S-10 state of the withdrawal.
 *
 * The confirmation names the EFFECT with the plan's own wording: "Retirar
 * participante libera su cupo en esta inscripción; no genera devolución"
 * (`frontend/04` §4). The action asks for a reason because it is audited.
 *
 * ## The action is DISABLED, and the reason is the TRUTH of the backend
 *
 * The ledger declares NO administrative withdrawal (`A0-UI04-04`): the
 * registered `DELETE /inscripciones/{id}/participantes/{participacion_id}`
 * (`RT-IN-06`) belongs to the RESPONSIBLE of his own inscription and the
 * module does NOT let the administrator group substitute for that
 * titularidad (`PoolOrchestrator._verificar_responsable`). It also carries no
 * reason, so it could not answer the audited action of the S-10.
 *
 * The button is disabled from the SAME registry that the service uses
 * (`RUTAS_ADMIN.retirarParticipante.registrado`): the interface and the
 * transport can never disagree about whether the route exists.
 */
export function DialogoRetirarParticipante({
  abierto,
  onAbiertoChange,
  nombreParticipante,
  inscripcionId,
  participacionId,
}: DialogoRetirarParticipanteProps) {
  const retirar = useRetirarParticipanteAdmin();

  const conectado = RUTAS_ADMIN.retirarParticipante.registrado;
  const listo = conectado && Boolean(inscripcionId) && Boolean(participacionId);
  const mensaje = retirar.error ? mensajeDeError(retirar.error) : undefined;
  const errorDeCampo = retirar.error
    ? erroresDeCampoDeError(retirar.error).motivo
    : undefined;

  return (
    <ConfirmacionIrreversible
      abierto={abierto}
      onAbiertoChange={onAbiertoChange}
      titulo={`Retirar a ${nombreParticipante}`}
      efecto="Retirar participante libera su cupo en esta inscripción; no genera devolución."
      motivo={{
        etiqueta: "Motivo de la retirada",
        placeholder: "Escribe el motivo que queda registrado en la auditoría.",
        requerido: true,
      }}
      confirmar={{
        etiqueta: "Retirar participante",
        deshabilitado: !listo,
        enCurso: retirar.isPending,
      }}
      error={mensaje}
      errorDeCampo={errorDeCampo}
      onConfirmar={(motivo) => {
        if (!inscripcionId || !participacionId) return;

        retirar.mutate({
          inscripcion_id: inscripcionId,
          participacion_id: participacionId,
          motivo,
        });
      }}
    />
  );
}
