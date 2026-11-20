import { PackageCheck } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { RUTAS } from "@/lib/routes";
import { ConfirmacionValidacion } from "../components/ConfirmacionValidacion";
import { ConsolaEscaner } from "../components/ConsolaEscaner";
import { VistaPreviaValidacion } from "../components/VistaPreviaValidacion";
import { estadoEntrega } from "../utils/validaciones.estados.utils";
import { formatearInstante } from "../utils/validaciones.fecha.utils";
import type {
  EntregaPendiente,
  EstadoVistaValidaciones,
  ResultadoValidacion,
  VistaPreviaValidacion as VistaPrevia,
} from "../types/validacion.types";

/**
 * ValidarEntregaView - `ADM-20`, the pickups of the store.
 *
 * A purchase of the store is not finished when it is paid: it is finished
 * when the buyer picks it up. This route is the queue of the pickups waiting
 * for a confirmation AND the confirmation itself.
 *
 * It is a DIFFERENT operation from the entrance control (`ADM-16`): the
 * subject is a paid order and not a right of entry. The two share the
 * presentation of the preview and nothing else (`GOV-02-RB-08c`).
 */
export function ValidarEntregaView({
  estado = "sin-datos",
  pendientes = [],
  vistaPrevia,
  resultado,
  onComprobar,
  onConfirmar,
  ocupado = false,
}: {
  estado?: EstadoVistaValidaciones;
  pendientes?: EntregaPendiente[];
  vistaPrevia?: VistaPrevia;
  resultado?: ResultadoValidacion;
  /** The check of a code. */
  onComprobar?: (codigo: string) => void;
  /** The confirmation of the delivery. */
  onConfirmar?: () => void;
  /** Whether an operation is in flight. */
  ocupado?: boolean;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-20"
        title="Validar las recogidas"
        description="Los pedidos comprados que todavía no se han recogido, con la persona que debe retirarlos y la confirmación de la entrega."
      />

      <AdminSubnav
        ariaLabel="Secciones de la tienda"
        items={[
          {
            href: RUTAS.administracion.marketplace,
            label: "Tienda",
            description: "Productos y pedidos",
          },
          {
            href: RUTAS.administracion.marketplaceInventario,
            label: "Inventario",
            description: "Movimientos de stock",
          },
          {
            href: RUTAS.administracion.marketplaceEntregas,
            label: "Entregas",
            description: "Recogidas por confirmar",
          },
        ]}
      />

      <AdminNotice title="Pagado y entregado son dos hechos">
        Un pedido pagado no es un pedido entregado. La entrega la registra una
        persona en el mostrador y queda anotada con su nombre y con el
        instante, nunca como una consecuencia automática del pago.
      </AdminNotice>

      {estado === "sin-permiso" ? (
        <ShellPermissionDenied title="No tienes permiso para registrar recogidas" />
      ) : estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar las recogidas"
          description="El servidor no respondió. Puedes volver a intentarlo; si el problema continúa, revisa el punto de control."
          accion={{ label: "Reintentar" }}
        />
      ) : (
        <>
          <AdminPanel
            title="Recogidas por confirmar"
            description="Los pedidos pagados a la espera de que la persona los retire."
          >
            {pendientes.length > 0 ? (
              <ul className="flex flex-col gap-3">
                {pendientes.map((pendiente) => {
                  const creado = formatearInstante(pendiente.created_at);
                  return (
                    <li
                      key={pendiente.pedido_id}
                      className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-mono text-xs text-muted-foreground">
                          {pendiente.pedido_id}
                        </span>
                        <span className="rounded-full border border-border bg-surface-recessed px-2.5 py-1 text-xs font-semibold text-foreground">
                          {estadoEntrega(pendiente.estado_entrega).etiqueta}
                        </span>
                      </div>
                      <ul className="flex flex-col gap-1">
                        {pendiente.lineas.map((linea) => (
                          <li
                            key={`${linea.tipo_concepto}-${linea.concepto_id}`}
                            className="flex items-center justify-between gap-2 text-sm"
                          >
                            <span className="text-foreground">
                              {linea.concepto_nombre}
                            </span>
                            <span className="text-muted-foreground tabular-nums">
                              {linea.cantidad}
                            </span>
                          </li>
                        ))}
                      </ul>
                      {creado ? (
                        <p className="text-caption text-muted-foreground">
                          <time dateTime={pendiente.created_at}>{creado}</time>
                        </p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <AdminEmptyState
                icon={PackageCheck}
                title="No hay recogidas pendientes"
                description="El servicio de recogidas todavía no está disponible en el backend, así que aquí no se dibuja ningún pedido. Cuando lo esté, se listarán los pedidos pagados a la espera de confirmación."
              />
            )}
          </AdminPanel>

          <AdminPanel
            title="Comprobación"
            description="Escribe o escanea el código del pedido para comprobar la recogida."
          >
            <ConsolaEscaner
              etiquetaCodigo="Código del pedido"
              ayuda="La comprobación no entrega nada: solo dice lo que responde el servidor."
              onComprobar={onComprobar}
              ocupado={ocupado}
              disabled={estado === "sin-datos"}
            />
          </AdminPanel>

          {vistaPrevia ? (
            <AdminPanel
              title="Vista previa"
              description="Lo que el servidor respondió del pedido, antes de registrar la entrega."
            >
              <VistaPreviaValidacion
                vistaPrevia={vistaPrevia}
                titulo="Vista previa de la recogida"
              />
            </AdminPanel>
          ) : null}

          <AdminPanel
            title="Confirmación"
            description="El acta de la entrega, con las unidades entregadas y el instante."
          >
            <ConfirmacionValidacion
              vistaPrevia={vistaPrevia}
              resultado={resultado}
              onConfirmar={onConfirmar}
              ocupado={ocupado}
              etiquetaAccion="Confirmar la entrega"
            />
          </AdminPanel>
        </>
      )}
    </div>
  );
}
