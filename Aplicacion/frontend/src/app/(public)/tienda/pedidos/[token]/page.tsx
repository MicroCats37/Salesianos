import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * SHOP-03 — Consultar el estado y la recogida de un pedido
 *
 * Shell de ruta (FND-06). La vista la construye UI-03.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return (
    <RoutePlaceholder
      pageId="SHOP-03"
      tarea="Consultar el estado y la recogida de un pedido"
      packet="UI-03"
    >
      <p className="font-mono text-xs text-muted-foreground">token: {token}</p>
    </RoutePlaceholder>
  );
}
