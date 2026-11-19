import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ADM-12 — Operar el cuadro de encuentros
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
      pageId="ADM-12"
      tarea="Operar el cuadro de encuentros"
      packet="UI-05"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
