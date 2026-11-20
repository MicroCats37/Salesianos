import { ScanLine } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-16 - the entrance control of the party.
 *
 * This is the surface of the person who scans a pass at the door: it
 * answers a single question —does this pass let this person in— and it
 * leaves the audit trail of every read.
 */
export function AdminPasesValidarView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-16"
        title="Controlar el ingreso a la fiesta"
        description="La validación de entradas: se comprueba el pase de una persona y se registra el resultado del acceso en el punto de control."
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.validaciones}>
              Ver la auditoría de accesos
            </Link>
          </Button>
        }
      />

      <AdminNotice title="El código es una credencial">
        El código que se escanea es una credencial en sí mismo: no se publica
        en la lista, no se copia en un registro y no se enseña en pantalla
        para que alguien más lo use.
      </AdminNotice>

      <AdminPanel
        title="Validación"
        description="El resultado de comprobar un pase: permitido o denegado, con su motivo."
      >
        <AdminEmptyState
          icon={ScanLine}
          title="Todavía no hay lecturas registradas"
          description="Las validaciones se leen del servicio de administración. Cuando la integración esté disponible, aquí se verá el resultado de cada lectura con su persona, su punto de acceso y su operador."
        />
      </AdminPanel>

      <AdminPanel
        title="Últimos accesos"
        description="Las últimas lecturas registradas en los puntos de control."
      >
        <AdminDataTable
          caption="Accesos registrados en los puntos de control"
          columns={[
            { key: "persona", label: "Persona" },
            { key: "resultado", label: "Resultado" },
            { key: "punto", label: "Punto de acceso" },
            { key: "operador", label: "Operador" },
            { key: "fecha", label: "Fecha y hora", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={ScanLine}
              title="Sin accesos registrados"
              description="Cada lectura de un pase deja una fila con su resultado, su punto de control, su operador y su hora."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
