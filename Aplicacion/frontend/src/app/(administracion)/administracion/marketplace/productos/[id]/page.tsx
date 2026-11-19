import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ADM-18 — Editar la galería y la oferta de un producto
 *
 * Shell de ruta (FND-06). La vista la construye UI-05.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <RoutePlaceholder
      pageId="ADM-18"
      tarea="Editar la galería y la oferta de un producto"
      packet="UI-05"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
