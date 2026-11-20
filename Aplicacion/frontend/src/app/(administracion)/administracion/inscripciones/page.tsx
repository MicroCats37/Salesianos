import { InscripcionesAdminRuta } from "@/features/admin/inscripciones";
import { parametrosDeConsulta } from "@/features/admin/operaciones/utils/parametros";

/**
 * ADM-05 — Gestionar las inscripciones
 *
 * Los filtros viven en la URL, así que la página lee la query string y la
 * pasa al contenedor. El contenedor es el que lee el dato y le entrega el
 * estado a la vista: la página sólo enruta.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;

  return <InscripcionesAdminRuta parametros={parametrosDeConsulta(params)} />;
}
