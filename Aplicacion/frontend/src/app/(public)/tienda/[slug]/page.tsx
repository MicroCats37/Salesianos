import { ProductoDetalleRuta } from "@/features/marketplace/views";

/**
 * SHOP-02 - Ver un producto y crear un pedido
 */
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  return <ProductoDetalleRuta slug={slug} />;
}
