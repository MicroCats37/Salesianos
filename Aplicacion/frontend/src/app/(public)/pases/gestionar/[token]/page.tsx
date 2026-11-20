import { PaseGestionarRuta } from "@/features/pases/views";

/**
 * PASS-02 - Asignar las personas beneficiarias de una compra
 *
 * El token viaja en la URL y ES la credencial: no hace falta sesión y la
 * ruta es pública por naturaleza.
 *
 * El backend abre el lote por su identificador
 * (`GET /pases/compras/{compra_pase_id}`) y el token solo no lo resuelve,
 * así que el enlace lleva las dos cosas: el token en la ruta y el
 * identificador del lote en la query.
 */
export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { token } = await params;
  const query = await searchParams;

  const bruto = query.compra;
  const compraPaseId = Array.isArray(bruto) ? bruto[0] : bruto;

  return <PaseGestionarRuta token={token} compraPaseId={compraPaseId} />;
}
