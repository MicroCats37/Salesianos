import { MisCompraDetalleView } from "@/features/cuenta/views";

/**
 * ACCOUNT-05 - Consultar el estado y el destino de una compra
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <MisCompraDetalleView id={id} />;
}
