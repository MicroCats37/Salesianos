import { parametrosDeConsulta } from "@/features/admin/operaciones/utils/parametros";
import { PagosAdminRuta } from "@/features/admin/pagos";

/**
 * ADM-14 — Investigar compras, órdenes y pagos
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

  return <PagosAdminRuta parametros={parametrosDeConsulta(params)} />;
}
