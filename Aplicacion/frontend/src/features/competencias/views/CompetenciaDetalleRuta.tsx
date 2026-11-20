"use client";

import { handleApiError } from "@/errors";
import { useCompetenciaDetalle } from "../hooks/useCompetencias";
import { CompetenciaDetalleView } from "./CompetenciaDetalleView";

export function CompetenciaDetalleRuta({ id }: { id: string }) {
  const consulta = useCompetenciaDetalle(id);
  const error = consulta.error ? handleApiError(consulta.error) : null;
  const estado = consulta.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : consulta.data
        ? "listo"
        : "sin-datos";

  return (
    <CompetenciaDetalleView id={id} estado={estado} detalle={consulta.data} />
  );
}
