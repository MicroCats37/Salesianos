import { AdminProductoDetalleView } from "@/features/admin/views";

/**
 * ADM-18 — Editar la galería y la oferta de un producto
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <AdminProductoDetalleView id={id} />;
}
