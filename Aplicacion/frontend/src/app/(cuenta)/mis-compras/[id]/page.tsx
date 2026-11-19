import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ACCOUNT-05 — Consultar el estado y el destino de una compra
 *
 * Shell de ruta (FND-06). La vista la construye UI-01.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <RoutePlaceholder
      pageId="ACCOUNT-05"
      tarea="Consultar el estado y el destino de una compra"
      packet="UI-01"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
