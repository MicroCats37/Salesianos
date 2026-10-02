import { Suspense } from "react";
import { InscripcionDetailView } from "@/features/inscripciones/views/InscripcionDetailView";

export default function DashboardInscripcionDetailPage() {
  return (
    <Suspense fallback={null}>
      <InscripcionDetailView />
    </Suspense>
  );
}
