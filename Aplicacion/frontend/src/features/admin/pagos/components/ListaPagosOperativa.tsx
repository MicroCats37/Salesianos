"use client";

import { useState } from "react";
import { BadgeCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  ListaOperativa,
  VeredictoConCausa,
} from "@/features/admin/operaciones";
import type { ColumnaOperativa, FilaOperativa } from "@/features/admin/operaciones";
import { DetalleComercialPago } from "./DetalleComercialPago";
import { DialogoAprobarPagoManual } from "./DialogoAprobarPagoManual";
import type {
  AdminPagoDetalleOut,
  AdminPagoListItemOut,
} from "../types/pagos-admin.types";

const COLUMNAS: ColumnaOperativa[] = [
  { key: "compra", label: "Compra", prioridad: 1, titular: true, identificador: true },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "total", label: "Total", prioridad: 1, numerico: true },
  { key: "concepto", label: "Concepto", prioridad: 2 },
  { key: "comprador", label: "Comprador", prioridad: 2 },
  { key: "tipo", label: "Tipo", prioridad: 2 },
  { key: "fecha", label: "Fecha", prioridad: 2 },
  { key: "accion", label: "Acción", prioridad: 2 },
];

/**
 * The code the presenter publishes when a purchase may be approved by hand.
 *
 * It is a CONTEXTUAL action: it appears only on the purchases the presenter
 * projects, never as a ubiquitous button of the list
 * (`GOV-02-RB-06` · explicitly forbidden).
 */
const CODIGO_APROBACION_MANUAL = "APROBACION_MANUAL";

export interface ListaPagosOperativaProps {
  /** The purchases of the operational list. */
  pagos: readonly AdminPagoListItemOut[];
  /** The commercial detail of each purchase, when it arrived. */
  detalles?: Readonly<Record<string, AdminPagoDetalleOut>>;
  /**
   * The verdict the list is filtered by.
   *
   * When the operator narrows the list to a verdict, the count is announced
   * in a live region (`GOV-02-RB-06` · accessibility intent).
   */
  filtroVeredicto?: string;
}

/**
 * ListaPagosOperativa - the FIRST level of `ADM-14`.
 *
 * The operational list shows ONE understandable state per row: the verdict
 * of the operator with its cause. The three facts that compose it —the state
 * of the purchase, the state of the order and the date of the payment— stay
 * in the drilldown, which is the diagnostic level.
 *
 * The browser NEVER recalculates the verdict (`GOV-02-RB-06a`).
 */
export function ListaPagosOperativa({
  pagos,
  detalles,
  filtroVeredicto,
}: ListaPagosOperativaProps) {
  const [aprobacionManual, setAprobacionManual] = useState<string | null>(null);

  const filas: FilaOperativa[] = pagos.map((pago) => ({
    id: pago.compra_id,
    celdas: {
      compra: pago.compra_id,
      estado: <VeredictoConCausa veredicto={pago.estado_operativo} />,
      total: `${pago.monto} ${pago.moneda}`,
      concepto: pago.resumen_concepto,
      comprador: pago.comprador.nombre,
      tipo: pago.tipo_compra,
      fecha: pago.fecha,
      accion: (
        <div className="flex flex-wrap items-center gap-2">
          <DetalleComercialPago
            pago={pago}
            detalle={detalles?.[pago.compra_id]}
          />
          {pago.acciones_disponibles.includes(CODIGO_APROBACION_MANUAL) ? (
            <Button
              variant="outline"
              size="sm"
              className="min-h-11"
              onClick={() => setAprobacionManual(pago.compra_id)}
            >
              <BadgeCheck className="size-4" aria-hidden="true" />
              Registrar pago externo
            </Button>
          ) : null}
        </div>
      ),
    },
  }));

  const pagoEnAprobacion = pagos.find(
    (pago) => pago.compra_id === aprobacionManual,
  );

  return (
    <div className="flex flex-col gap-4">
      {filtroVeredicto ? (
        <p role="status" className="sr-only">
          {filas.length} compras con el estado seleccionado.
        </p>
      ) : null}

      <ListaOperativa
        caption="Compras, órdenes de pago y su veredicto"
        columnas={COLUMNAS}
        filas={filas}
      />

      <DialogoAprobarPagoManual
        abierto={aprobacionManual !== null}
        onAbiertoChange={(abierto) => {
          if (!abierto) setAprobacionManual(null);
        }}
        concepto={pagoEnAprobacion?.resumen_concepto ?? "la compra"}
        monto={pagoEnAprobacion?.monto ?? "0.00"}
        moneda={pagoEnAprobacion?.moneda ?? "PEN"}
        ordenPagoId={pagoEnAprobacion?.orden_pago_id ?? undefined}
      />
    </div>
  );
}
