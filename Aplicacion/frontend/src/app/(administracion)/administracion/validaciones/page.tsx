import { AuditoriaValidacionesView } from "@/features/validaciones/views";

/**
 * ADM-22 - Auditar ingresos, entregas e incidencias
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ veredicto?: string }>;
}) {
  const { veredicto } = await searchParams;

  return <AuditoriaValidacionesView filtroVeredicto={veredicto} />;
}
