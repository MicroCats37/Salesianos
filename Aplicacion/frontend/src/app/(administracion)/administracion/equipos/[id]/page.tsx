import { EquipoAdminDetalleRuta } from "@/features/admin/equipos";

/**
 * ADM-08 — Operar un equipo: plantilla y elegibilidad
 *
 * El contenedor es el que lee el dato y le entrega el estado a la vista: la
 * página sólo enruta.
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <EquipoAdminDetalleRuta id={id} />;
}
