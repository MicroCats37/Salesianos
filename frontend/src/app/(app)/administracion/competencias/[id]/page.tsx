import { Suspense } from "react";
import { CompetenciasDetalle } from "@/features/admin/competencias";

/**
 * Detail of ONE competition.
 *
 * The page only resolves the identifier of the route: the feature owns the
 * data, the teams and the rounds.
 */
export default async function CompetenciaDetallePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <Suspense fallback={null}>
      <CompetenciasDetalle competenciaId={id} />
    </Suspense>
  );
}
