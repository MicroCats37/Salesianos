import { Suspense } from "react";
import { CompetenciasLista } from "@/features/admin/competencias";

/**
 * List of the competitions of the administrative scope.
 *
 * The page is a thin composition: the guard lives in the layout and the
 * feature owns the data, the filters and the states.
 */
export default function CompetenciasPage() {
  return (
    <Suspense fallback={null}>
      <CompetenciasLista />
    </Suspense>
  );
}
