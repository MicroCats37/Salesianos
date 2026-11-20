"use client";

import { handleApiError } from "@/errors";
import {
  useCompetenciaCuadro,
  useCompetenciaDetalle,
  useGenerarCuadro,
} from "../hooks/useCompetencias";
import { CompetenciaCuadroView } from "./CompetenciaCuadroView";

export function CompetenciaCuadroRuta({ id }: { id: string }) {
  const consulta = useCompetenciaCuadro(id);
  const detalle = useCompetenciaDetalle(id);
  const generar = useGenerarCuadro();
  const error = consulta.error ? handleApiError(consulta.error) : null;
  const estado = consulta.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : "listo";

  return (
    <CompetenciaCuadroView
      id={id}
      estado={estado}
      rondas={consulta.data ?? []}
      equipos={detalle.data?.equipos ?? []}
      generarCuadro={() => generar.mutateAsync(id)}
      generando={generar.isPending}
    />
  );
}
