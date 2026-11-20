import { parametrosDeConsulta } from "@/features/admin/operaciones/utils/parametros";
import { AdminResumenRuta } from "@/features/admin/resumen";

/**
 * ADM-01: the state of the edition in force
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

  return <AdminResumenRuta parametros={parametrosDeConsulta(params)} />;
}
