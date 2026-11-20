"use client";

import { handleApiError } from "@/errors";
import {
  useAsignarBeneficiario,
  useCompraPaseDetalle,
  useRevocarBeneficiario,
} from "../hooks";
import type {
  EstadoVistaPases,
  EnviarAsignacionPase,
  RevocarBeneficiario,
} from "../types/pase.types";
import { adaptarCompra } from "../utils/pase.adaptador.utils";
import { PaseGestionarView } from "./PaseGestionarView";

export interface PaseGestionarRutaProps {
  /** The private token of the link. It IS the credential. */
  token: string;
  /**
   * The identifier of the batch, read from the link.
   *
   * The backend opens a batch by its identifier and the token alone does not
   * resolve it (`GET /pases/compras/{compra_pase_id}`), so the link carries
   * both.
   */
  compraPaseId?: string;
}

/**
 * The container of `PASS-02`.
 *
 * The link opens ONE batch and the token is the credential. The denial is
 * NEUTRAL (`QA-U03`): a 401 (an expired, revoked or unknown token), a 403
 * (a token that does not authorize this batch) and a 404 (a batch that does
 * not exist) answer the SAME message, so the link never reveals whether a
 * purchase exists.
 */
export function PaseGestionarRuta({
  token,
  compraPaseId,
}: PaseGestionarRutaProps) {
  const consulta = useCompraPaseDetalle(compraPaseId, token);
  const asignacion = useAsignarBeneficiario(compraPaseId ?? "", token);
  const revocacion = useRevocarBeneficiario(compraPaseId ?? "", token);

  const error = consulta.error ? handleApiError(consulta.error) : null;

  const estado: EstadoVistaPases = !compraPaseId
    ? "sin-permiso"
    : consulta.isPending
      ? "cargando"
      : error
        ? error.status === 401 ||
            error.status === 403 ||
            error.status === 404
          ? "sin-permiso"
          : "error"
        : consulta.data
          ? "listo"
          : "sin-datos";

  const compra = consulta.data ? adaptarCompra(consulta.data) : undefined;

  /** The assignment of a pass to a person. */
  const asignar: EnviarAsignacionPase = async (datos) => {
    await asignacion.mutateAsync(datos);
  };

  /** The revocation of an entry right. */
  const revocar: RevocarBeneficiario = async (beneficiario, motivo) => {
    await revocacion.mutateAsync({
      persona_id: beneficiario.persona_id,
      motivo,
    });
  };

  return (
    <PaseGestionarView
      token={token}
      estado={estado}
      compra={compra}
      mensajeError={error?.message}
      asignar={asignar}
      revocar={revocar}
      reintentar={() => void consulta.refetch()}
    />
  );
}
