import { Suspense } from "react";
import { CompetenciasAgenda } from "@/features/admin/competencias";

/**
 * Temporal agenda of ONE day.
 *
 * The day lives in the URL: the page only wraps the view in a boundary and
 * the feature owns the data, the filters and the states.
 */
export default function CompetenciasAgendaPage() {
  return (
    <Suspense fallback={null}>
      <CompetenciasAgenda />
    </Suspense>
  );
}
