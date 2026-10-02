import { Suspense } from "react";
import { InscripcionClientShell } from "@/features/inscripciones/views/InscripcionClientShell";

export default function InscripcionPage() {
  return (
    <Suspense fallback={null}>
      <InscripcionClientShell />
    </Suspense>
  );
}
