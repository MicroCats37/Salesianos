"use client";

import { handleApiError } from "@/errors";
import { useCompraPase, useCatalogoPases } from "../hooks";
import type {
  EstadoVistaPases,
  EnviarCompraPase,
} from "../types/pase.types";
import { PasesView } from "./PasesView";

/**
 * The container of `PASS-01`.
 *
 * The page (`src/app/(public)/pases/page.tsx`) is ROUTING-ONLY: this
 * container owns the read of the catalogue and the mutation of the purchase,
 * and the VIEW owns the drawing.
 *
 * It never decides anything: the catalogue is the answer of the server, the
 * price is the one the server sent and the state of the purchase is the one
 * the server froze.
 */
export function PasesRuta() {
  const consulta = useCatalogoPases();
  const compra = useCompraPase();

  const error = consulta.error ? handleApiError(consulta.error) : null;

  const estado: EstadoVistaPases = consulta.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : consulta.data
        ? "listo"
        : "sin-datos";

  /**
   * The purchase.
   *
   * The payload is built by the mutation, not here: the container only says
   * WHICH pass, HOW MANY and WHAT the buyer typed.
   */
  const enviar: EnviarCompraPase = async (pase, cantidad, datos) => {
    const creada = await compra.mutateAsync({
      pase_id: pase.id,
      cantidad,
      datos,
    });

    return creada;
  };

  return (
    <PasesView
      estado={estado}
      catalogo={consulta.data}
      mensajeError={error?.message}
      enviar={enviar}
      reintentar={() => void consulta.refetch()}
    />
  );
}
