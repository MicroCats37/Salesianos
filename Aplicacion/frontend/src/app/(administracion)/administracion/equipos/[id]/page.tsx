import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ADM-08 — Operar un equipo: plantilla y elegibilidad
 *
 * Shell de ruta (FND-06). La vista la construye UI-04.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <RoutePlaceholder
      pageId="ADM-08"
      tarea="Operar un equipo: plantilla y elegibilidad"
      packet="UI-04"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
