import { Suspense } from "react";
import { AdminEquiposLista } from "@/features/admin/components";

/**
 * Operational teams table (A7).
 */
export default function AdminEquiposPage() {
  return (
    <Suspense fallback={null}>
      <AdminEquiposLista />
    </Suspense>
  );
}
