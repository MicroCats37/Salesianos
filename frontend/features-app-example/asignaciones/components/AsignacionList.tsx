"use client";

import { useAsignaciones } from "../hooks/useAsignaciones";

/**
 * AsignacionList - placeholder component for asignaciones list.
 * Components handle ZERO raw error logic - errors flow through error handler.
 */
export function AsignacionList() {
  const { data: asignaciones, isLoading } = useAsignaciones();

  if (isLoading) {
    return <div>Cargando asignaciones...</div>;
  }

  return (
    <div>
      <h1>Asignaciones</h1>
      {/* Implementation comes later */}
    </div>
  );
}
