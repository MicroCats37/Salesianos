import { Suspense } from "react";
import { CompetenciasCuadro } from "@/features/admin/competencias";

/**
 * Bracket of ONE competition.
 *
 * The competition lives in the URL (`?id=`), so the page only wraps the view
 * in a boundary: the feature owns the data and the grid.
 */
export default function CompetenciasCuadroPage() {
  return (
    <Suspense fallback={null}>
      <CompetenciasCuadro />
    </Suspense>
  );
}
