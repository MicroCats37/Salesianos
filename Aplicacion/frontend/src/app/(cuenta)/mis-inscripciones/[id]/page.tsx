import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * ACCOUNT-03 — Gestionar una inscripción, su pool y sus equipos
 *
 * Shell de ruta (FND-06). La vista la construye UI-02.
 */

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <RoutePlaceholder
      pageId="ACCOUNT-03"
      tarea="Gestionar una inscripción, su pool y sus equipos"
      packet="UI-02"
    >
      <p className="font-mono text-xs text-muted-foreground">id: {id}</p>
    </RoutePlaceholder>
  );
}
