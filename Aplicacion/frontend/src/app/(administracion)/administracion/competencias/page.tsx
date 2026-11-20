import { CompetenciasListaView } from "@/features/competencias/views";

/**
 * ADM-10 - Seleccionar y administrar competencias
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ estado?: string }>;
}) {
  const { estado } = await searchParams;

  return <CompetenciasListaView filtroEstado={estado} />;
}
