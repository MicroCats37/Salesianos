"use client";

import { useTramites } from "../hooks/useTramites";

/**
 * TramiteList - placeholder component for tramites list.
 * Components handle ZERO raw error logic - errors flow through error handler.
 */
export function TramiteList() {
  const { data: tramites, isLoading } = useTramites();

  if (isLoading) {
    return <div>Cargando trámites...</div>;
  }

  return (
    <div>
      <h1>Trámites</h1>
      {/* Implementation comes later */}
    </div>
  );
}
