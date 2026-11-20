import { CompetenciaDetalleView } from "@/features/competencias/views";

/**
 * ADM-11 - Ver la ficha operativa de una competencia
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <CompetenciaDetalleView id={id} />;
}
