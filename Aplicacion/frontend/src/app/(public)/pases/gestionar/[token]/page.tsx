import { RoutePlaceholder } from "@/components/shell/RoutePlaceholder";

/**
 * PASS-02 — Asignar las personas beneficiarias de una compra
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
      pageId="PASS-02"
      tarea="Asignar las personas beneficiarias de una compra"
      packet="UI-03"
    >
      <p className="font-mono text-xs text-muted-foreground">token: {token}</p>
    </RoutePlaceholder>
  );
}
