import { InscripcionListTable } from "@/features/admin/inscripciones/components";

export default function AdminInscripcionesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-[#17214b]">Inscripciones</h1>
        <p className="mt-1 text-muted-foreground">
          Revisa y gestiona las solicitudes de preinscripción.
        </p>
      </div>
      <InscripcionListTable />
    </div>
  );
}
