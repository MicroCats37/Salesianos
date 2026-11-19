import { Suspense } from "react";
import { RegisterClientShell } from "@/features/auth/views/RegisterClientShell";

/**
 * AUTH-02 — Crear una cuenta de responsable
 *
 * El formulario resuelve el documento antes de pedir los datos de la
 * persona: son cuatro bloques, no dos campos, y por eso no es un signup de
 * shadcn.
 */
export default function RegistroPage() {
  return (
    <Suspense fallback={null}>
      <RegisterClientShell />
    </Suspense>
  );
}
