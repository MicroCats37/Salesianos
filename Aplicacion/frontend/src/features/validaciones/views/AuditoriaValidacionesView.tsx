import { ScrollText } from "lucide-react";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import { RUTAS } from "@/lib/routes";
import {
  FiltrosAuditoria,
  TablaAuditoriaValidaciones,
} from "../components/TablaAuditoriaValidaciones";
import type {
  EstadoVistaValidaciones,
  RegistroValidacion,
} from "../types/validacion.types";

/**
 * AuditoriaValidacionesView - `ADM-22`, the transversal audit.
 *
 * This route is the memory of the edition: the entrances, the pickups and
 * the incidents, in the order they happened. It is the surface an operator
 * opens when something has to be explained.
 *
 * The audit is TRANSVERSAL: it lists the entries AND the pickups of the
 * store, and it NEVER mixes them with a payment confirmation
 * (`GOV-02-RB-08c`).
 */
export function AuditoriaValidacionesView({
  estado = "sin-datos",
  registros = [],
  filtroVeredicto,
}: {
  estado?: EstadoVistaValidaciones;
  registros?: RegistroValidacion[];
  /** The verdict filter of the URL, if there is one. */
  filtroVeredicto?: string;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-22"
        title="Auditar ingresos, entregas e incidencias"
        description="El rastro de lo que ha pasado en la edición: los accesos a la fiesta, las recogidas de la tienda y las incidencias registradas."
      />

      <AdminNotice title="El registro no se reescribe">
        La auditoría es de solo lectura y conserva el orden de los hechos.
        Una incidencia se corrige con un asiento nuevo, nunca editando el
        anterior.
      </AdminNotice>

      <AdminPanel
        title="Bitácora"
        description="Los asientos del registro, del más reciente al más antiguo."
        actions={
          <FiltrosAuditoria
            veredicto={filtroVeredicto}
            accion={RUTAS.administracion.validaciones}
          />
        }
      >
        {estado === "listo" ? (
          <TablaAuditoriaValidaciones
            registros={registros}
            filtroVeredicto={filtroVeredicto}
            accion={RUTAS.administracion.validaciones}
          />
        ) : estado === "cargando" ? (
          <div role="status" aria-live="polite" className="flex flex-col gap-3">
            <span className="sr-only">Cargando la auditoría…</span>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : estado === "sin-permiso" ? (
          <ShellPermissionDenied title="No tienes permiso para ver la auditoría" />
        ) : estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar la auditoría"
            description="El servidor no devolvió los asientos del registro. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            accion={{ label: "Reintentar" }}
          />
        ) : (
          <AdminEmptyState
            icon={ScrollText}
            title="Todavía no hay asientos en la bitácora"
            description="El servicio de auditoría de validaciones todavía no está disponible en el backend, así que aquí no se dibuja ningún asiento. Cuando lo esté, se listarán los ingresos y las recogidas con su resultado, su punto de control y su responsable."
          />
        )}
      </AdminPanel>
    </div>
  );
}
