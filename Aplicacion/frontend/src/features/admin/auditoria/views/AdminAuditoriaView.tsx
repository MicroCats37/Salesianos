import { ScrollText } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import type { EstadoAuditoriaAdmin } from "../types/auditoria-admin.types";

/**
 * ADM-15: the acta of the sensitive actions.
 *
 * The acta is a READING surface: it never writes. Its content is the trail
 * that the backend published — WHO, WHEN, WHAT and WHY — and nothing else.
 *
 * ## What the browser does NOT do
 *
 * - It does NOT invent an entry: the list is the one the server published.
 * - It does NOT judge an action: the reason is printed verbatim, with the
 *   code the server declared.
 * - It does NOT reconstruct the context of the action: the acta publishes a
 *   white list and the raw context never travels.
 */
export function AdminAuditoriaView({
  estado,
}: {
  estado: EstadoAuditoriaAdmin;
}) {
  const listo = estado.estado === "listo";

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-15"
        title="Acta de las acciones sensibles"
        description="Cada comando sensible deja constancia de quién lo ejecutó, cuándo, qué tocó y por qué. El motivo es obligatorio: sin motivo el comando no se ejecuta."
      />

      <AdminNotice title="El acta no expone el contexto crudo">
        El backend sanea el contexto al escribirlo y publica una lista blanca al
        leerlo: aquí no hay secretos, ni tokens, ni cargas útiles del proveedor.
      </AdminNotice>

      <AdminPanel
        title="Actas registradas"
        description="De la más reciente a la más antigua."
      >
        {listo ? (
          <AdminDataTable
            caption="Actas de las acciones sensibles"
            columns={[
              { key: "momento", label: "Momento" },
              { key: "actor", label: "Actor" },
              { key: "accion", label: "Acción" },
              { key: "entidad", label: "Entidad" },
              { key: "motivo", label: "Motivo" },
            ]}
            filas={estado.datos.items.map((acta) => ({
              cells: {
                momento: (
                  <span className="whitespace-nowrap tabular-nums text-muted-foreground">
                    {acta.registrado_en}
                  </span>
                ),
                actor: (
                  <span className="font-medium text-foreground">
                    {acta.actor}
                  </span>
                ),
                accion: (
                  <span className="text-xs font-semibold text-muted-foreground">
                    {acta.accion}
                  </span>
                ),
                entidad: (
                  <span className="text-sm text-muted-foreground">
                    {acta.entidad}
                  </span>
                ),
                motivo: (
                  <span className="whitespace-normal text-foreground">
                    {acta.motivo}
                  </span>
                ),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={ScrollText}
                title="Todavía no hay actas"
                description="Ninguna acción sensible se ha registrado en esta edición."
              />
            }
          />
        ) : (
          <AdminEmptyState
            icon={ScrollText}
            title={tituloDelEstado(estado.estado)}
            description={descripcionDelEstado(estado)}
          />
        )}
      </AdminPanel>
    </div>
  );
}

function tituloDelEstado(estado: string): string {
  if (estado === "cargando") return "Cargando el acta";
  if (estado === "sin-permiso") {
    return "No tienes autorización para ver el acta";
  }
  if (estado === "error") return "No se pudo leer el acta";
  return "Todavía no hay un acta enlazada";
}

function descripcionDelEstado(estado: {
  estado: string;
  mensaje?: string;
}): string {
  if (estado.estado === "sin-datos") {
    return "El acta se apoya en la edición que resuelve el backend. Cuando la ruta esté registrada, aquí se verán las acciones sensibles y su motivo.";
  }

  return estado.mensaje ?? "El backend no pudo responder.";
}
