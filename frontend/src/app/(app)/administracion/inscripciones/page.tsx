import { Suspense } from "react";
import { AdminInscripcionesLista } from "@/features/admin/components";

/**
 * Operational registrations table (A3).
 *
 * The page is a thin composition: the guard lives in the layout and the
 * administration feature owns the data, the filters and the states.
 */
export default function AdminInscripcionesPage() {
  return (
    <Suspense fallback={null}>
      <AdminInscripcionesLista />
    </Suspense>
  );
}
