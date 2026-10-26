import { Suspense } from "react";
import { AdminUsuariosLista } from "@/features/admin/components";

/**
 * Read-only accounts table (A13) with the drilldown of one account (A14).
 */
export default function AdminUsuariosPage() {
  return (
    <Suspense fallback={null}>
      <AdminUsuariosLista />
    </Suspense>
  );
}
