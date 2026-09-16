"use client";

import { useTramite } from "../hooks/useTramites";

interface TramiteDetailProps {
  id: string;
}

/**
 * TramiteDetail - placeholder component for tramite detail view.
 * Components handle ZERO raw error logic - errors flow through error handler.
 */
export function TramiteDetail({ id }: TramiteDetailProps) {
  const { data: tramite, isLoading } = useTramite(id);

  if (isLoading) {
    return <div>Cargando trámite...</div>;
  }

  return (
    <div>
      <h1>Detalle de Trámite {id}</h1>
      {tramite && <p>Expediente: {tramite.expediente?.asunto}</p>}
      {/* Implementation comes later */}
    </div>
  );
}
