"use client";

import { isAxiosError } from "axios";
import { Lock, PackageSearch } from "lucide-react";
import { useState } from "react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { ShellErrorState } from "@/components/shell/ShellState";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { EstadoPagoTienda, IzipayPedidoModal } from "../components";
import { usePedidoSeguimiento } from "../hooks";
import type {
  EstadoDeclarado,
  EstadoVistaTienda,
  SeguimientoPedido,
  VeredictoPago,
} from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";

function adaptarPago(codigo: string): VeredictoPago {
  if (["CONFIRMADO", "PAGADO", "PAGADA", "EXITO"].includes(codigo)) {
    return {
      estado: {
        codigo,
        etiqueta: "Pago confirmado",
        descripcion: "Tu pago fue confirmado por el proveedor.",
      },
      rol: "confirmado",
    };
  }
  if (["FALLIDO", "CANCELADO", "NO_COMPLETADO"].includes(codigo)) {
    return {
      estado: {
        codigo,
        etiqueta: "Pago no completado",
        descripcion:
          "Puedes intentar el pago nuevamente si el pedido sigue vigente.",
      },
      rol: "sin-confirmar",
    };
  }
  if (["EN_VERIFICACION", "VERIFICANDO"].includes(codigo)) {
    return {
      estado: {
        codigo,
        etiqueta: "Pago en verificación",
        descripcion: "Estamos esperando la confirmación del proveedor.",
      },
      rol: "verificando",
    };
  }
  return {
    estado: {
      codigo,
      etiqueta: "Pago pendiente",
      descripcion: "Puedes continuar con el pago seguro cuando estés listo.",
    },
    rol: "pendiente",
  };
}

function adaptarEntrega(codigo: string): EstadoDeclarado {
  if (codigo === "ENTREGADO") return { codigo, etiqueta: "Entregado" };
  if (codigo === "LISTO") return { codigo, etiqueta: "Listo para recoger" };
  return { codigo, etiqueta: "Pendiente de recogida" };
}

export interface PedidoSeguimientoViewProps {
  /** The private token of the link. It IS the credential. */
  token: string;
  /** The state of the order. */
  estado?: EstadoVistaTienda;
  /** The order, when the link opens it. */
  pedido?: SeguimientoPedido;
  /** The payment verdict, resolved by the adapter. */
  pago?: VeredictoPago;
  /** The delivery state, resolved by the adapter. */
  entrega?: EstadoDeclarado;
}

/**
 * SHOP-03 - the state of an order and its pickup.
 *
 * The route is reached with a token in the URL: the token IS the credential
 * and it opens exactly one order. The visitor does not need a session, and
 * the page never shows an order that the token does not open.
 *
 * **The payment state and the delivery state are TWO different facts and TWO
 * different lines** (`RN-M07`, `QA-M04`): a paid order that has not been
 * delivered never reads as "delivered".
 */
export function PedidoSeguimientoView({
  token,
  estado,
  pedido,
  pago,
  entrega,
}: PedidoSeguimientoViewProps) {
  const [pagoAbierto, setPagoAbierto] = useState(false);
  const consulta = usePedidoSeguimiento(token);
  const pedidoActual = pedido ?? consulta.data;
  const estadoVista: EstadoVistaTienda =
    estado ??
    (consulta.isPending
      ? "cargando"
      : consulta.isError
        ? isAxiosError(consulta.error) &&
          consulta.error.response?.status === 403
          ? "sin-permiso"
          : "error"
        : pedidoActual
          ? "listo"
          : "sin-datos");
  const pagoActual =
    pago ?? (pedidoActual ? adaptarPago(pedidoActual.estado_pago) : undefined);
  const entregaActual =
    entrega ??
    (pedidoActual ? adaptarEntrega(pedidoActual.estado_entrega) : undefined);
  const puedePagar =
    pagoActual?.rol === "pendiente" || pagoActual?.rol === "sin-confirmar";

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SHOP-03"
        title="Estado de tu pedido"
        description="El pedido, su estado de pago y su recogida. El enlace que recibiste abre únicamente este pedido."
        facts={[{ label: "Acceso", value: `${token.slice(0, 8)}...` }]}
      />

      {estadoVista === "sin-permiso" ? (
        <Alert>
          <Lock className="size-4" aria-hidden="true" />
          <AlertTitle>No pudimos abrir este pedido</AlertTitle>
          <AlertDescription>
            El enlace puede haber caducado o no corresponde a este pedido. Si lo
            has perdido, puedes pedir un enlace nuevo para recuperarlo.
          </AlertDescription>
        </Alert>
      ) : null}

      {estadoVista === "error" ? (
        <ShellErrorState
          title="No pudimos comprobar tu enlace"
          description="No pudimos comprobar el enlace en este momento. Vuelve a intentarlo en unos segundos."
          className="min-h-11"
        />
      ) : null}

      {estadoVista === "cargando" ? (
        <RouteEmptyState
          icon={PackageSearch}
          title="Abriendo tu pedido"
          description="Estamos comprobando el enlace privado y el estado más reciente de tu pedido."
        />
      ) : null}

      {estadoVista === "sin-datos" ? (
        <RouteEmptyState
          icon={PackageSearch}
          title="Este pedido todavía no se puede mostrar"
          description="El servicio de pedidos de la tienda todavía no está publicado, así que aquí no se puede abrir ningún pedido. En cuanto lo esté, este enlace abrirá el pedido con su estado de compra, su estado de orden y su evidencia de pago. La interfaz no afirma un pago que el proveedor no ha confirmado."
        />
      ) : null}

      {estadoVista === "listo" && pedidoActual ? (
        <>
          <section
            aria-labelledby="estados-pedido-titulo"
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <h2
              id="estados-pedido-titulo"
              className="text-section-title text-foreground"
            >
              Estado del pedido
            </h2>

            <dl className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted-foreground">Pago</dt>
                <dd>
                  {pagoActual ? (
                    <EstadoPagoTienda
                      veredicto={pagoActual}
                      conDescripcion
                      accion={
                        puedePagar
                          ? {
                              etiqueta: "Pagar con Izipay",
                              onClick: () => setPagoAbierto(true),
                            }
                          : undefined
                      }
                    />
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      Todavía no hay un veredicto de pago.
                    </span>
                  )}
                </dd>
              </div>

              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted-foreground">Entrega</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {entregaActual
                    ? entregaActual.etiqueta
                    : "Sin estado de entrega"}
                </dd>
              </div>
            </dl>

            <p className="text-caption text-muted-foreground">
              Pagar el pedido no lo entrega: la recogida se confirma en el punto
              de control del evento.
            </p>
          </section>

          <section
            aria-labelledby="productos-pedido-titulo"
            className="flex flex-col gap-3"
          >
            <h2
              id="productos-pedido-titulo"
              className="text-section-title text-foreground"
            >
              Productos
            </h2>

            <ul className="flex flex-col gap-2">
              {pedidoActual.lineas.map((linea) => (
                <li
                  key={`${linea.concepto_id}-${linea.tipo_concepto}`}
                  className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised px-3 py-2"
                >
                  <span className="text-sm text-foreground">
                    {`${linea.cantidad} x ${linea.concepto_nombre}`}
                  </span>
                  <span className="text-sm font-semibold tabular-nums text-foreground">
                    {formatearMonto(linea.subtotal, pedidoActual.moneda)}
                  </span>
                </li>
              ))}
            </ul>

            <p className="text-sm font-semibold tabular-nums text-foreground">
              {`Total: ${formatearMonto(pedidoActual.total, pedidoActual.moneda)}`}
            </p>
          </section>
        </>
      ) : null}

      <IzipayPedidoModal
        abierto={pagoAbierto}
        token={token}
        onCerrar={() => setPagoAbierto(false)}
        onEstadoActualizado={() => consulta.refetch()}
      />
    </div>
  );
}
