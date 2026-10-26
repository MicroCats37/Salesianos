import { Suspense } from "react";
import { AdminInscripcionDetalle } from "@/features/admin/components";

/**
 * Drilldown of one registration (A4).
 *
 * The page only resolves the identifier of the route: the administration
 * feature owns the data and the six documented blocks.
 */
export default async function AdminInscripcionDetallePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <Suspense fallback={null}>
      <AdminInscripcionDetalle inscripcionId={id} />
    </Suspense>
  );
}
