import { InscripcionAdminDetalleRuta } from "@/features/admin/inscripciones";

/**
 * ADM-06 — Operar una inscripción: pool, equipos y compras
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

  return <InscripcionAdminDetalleRuta id={id} />;
}
