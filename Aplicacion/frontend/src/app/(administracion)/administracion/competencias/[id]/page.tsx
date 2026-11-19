import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ADM-11 — Ver la ficha operativa de una competencia
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
      pageId="ADM-11"
      tarea="Ver la ficha operativa de una competencia"
      packet="UI-05"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
