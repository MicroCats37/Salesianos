import type { Metadata } from "next";
import { InscripcionWizard } from "@/features/inscripcion/components/InscripcionWizard";
import { requireRole } from "@/lib/auth/require-role";

export const metadata: Metadata = {
  title: "Inscripción · Salesianos FEST 2026",
};

export default async function InscripcionPage() {
  await requireRole("responsable");

  return (
    <main className="min-h-screen p-8 bg-[#f4f6fb]">
      <InscripcionWizard />
    </main>
  );
}
