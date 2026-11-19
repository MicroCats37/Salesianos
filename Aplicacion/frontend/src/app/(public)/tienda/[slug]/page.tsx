import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * SHOP-02 — Ver un producto y crear un pedido
 *
 * Shell de ruta (FND-06). La vista la construye UI-03.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <RoutePlaceholder
      pageId="SHOP-02"
      tarea="Ver un producto y crear un pedido"
      packet="UI-03"
    >
      <p className="font-mono text-xs text-muted-foreground">slug: {slug}</p>
    </RoutePlaceholder>
  );
}
