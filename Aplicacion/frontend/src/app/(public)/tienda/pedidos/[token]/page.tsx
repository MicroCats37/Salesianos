import { PedidoSeguimientoView } from "@/features/marketplace/views";

/**
 * SHOP-03 - Consultar el estado y la recogida de un pedido
 *
 * El token viaja en la URL y ES la credencial: abre un único pedido y la
 * ruta es pública por naturaleza.
 */
export default async function Page({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  return <PedidoSeguimientoView token={token} />;
}
