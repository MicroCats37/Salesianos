"use client";

import { useAsignacion } from "../hooks/useAsignaciones";

interface AsignacionDetailProps {
  id: string;
}

/**
 * AsignacionDetail - placeholder component for asignacion detail view.
 * Components handle ZERO raw error logic - errors flow through error handler.
 */
export function AsignacionDetail({ id }: AsignacionDetailProps) {
  const { data: asignacion, isLoading } = useAsignacion(id);

  if (isLoading) {
    return <div>Cargando asignación...</div>;
  }

  return (
    <div>
      <h1>Asignación #{asignacion?.id}</h1>
      {/* Implementation comes later */}
    </div>
  );
}
