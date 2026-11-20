"use client";

import {
  ChevronDown,
  CreditCard,
  ExternalLink,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { ExplicacionVeredicto } from "@/features/admin/operaciones";
import type {
  AdminPagoDetalleOut,
  PagoOperativoOut,
} from "../types/pagos-admin.types";

export interface DetalleComercialPagoProps {
  /** The purchase as the operational list published it. */
  pago: PagoOperativoOut;
  /**
   * The detail of the purchase, when it arrived.
   *
   * While the detail is not connected, the sheet says so instead of drawing
   * a diagnosis that does not exist.
   */
  detalle?: AdminPagoDetalleOut;
}

/**
 * DetalleComercialPago - the SECOND and the THIRD level of `ADM-14`.
 *
 * Level 2 (commercial detail): what was bought, the state of the payment,
 * what was obtained and the next permitted action.
 *
 * Level 3 (diagnosis and audit): the order, the attempts of the provider,
 * the evidence and the manual operations. It is HIDDEN BY DEFAULT under a
 * disclosure, because the provider layer is technical detail and it never
 * inherits a verdict colour: the state of an attempt is TEXT inside the
 * collapsed diagnosis, never a chip (`GOV-02-RB-06` · semantic-token intent).
 */
export function DetalleComercialPago({
  pago,
  detalle,
}: DetalleComercialPagoProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="min-h-11">
          <CreditCard className="size-4" aria-hidden="true" />
          Ver compra
        </Button>
      </SheetTrigger>
      <SheetContent
        side="right"
        showCloseButton={false}
        className="w-full sm:max-w-lg overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle>{pago.resumen_concepto}</SheetTitle>
          <SheetDescription>
            Compra {pago.compra_id} · {pago.tipo_compra} ·{" "}
            {pago.comprador.nombre}
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-5 px-4">
          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              Estado del pago
            </h3>
            <ExplicacionVeredicto veredicto={pago.estado_operativo} />
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              Lo que obtuvo
            </h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {pago.entrega_derechos.etiqueta}
            </p>
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              Siguiente acción permitida
            </h3>
            {detalle?.siguiente_accion ? (
              <Button variant="outline" className="min-h-11 justify-start">
                <ExternalLink className="size-4" aria-hidden="true" />
                {detalle.siguiente_accion.etiqueta}
              </Button>
            ) : (
              <p className="text-sm leading-relaxed text-muted-foreground">
                No hay ninguna acción habilitada para esta compra.
              </p>
            )}
          </section>

          <section className="flex flex-col gap-2">
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="min-h-11 justify-between">
                  <span className="inline-flex items-center gap-2">
                    <Stethoscope className="size-4" aria-hidden="true" />
                    Diagnóstico y auditoría
                  </span>
                  <ChevronDown className="size-4" aria-hidden="true" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="flex flex-col gap-4 pt-3">
                {!detalle ? (
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    El detalle técnico de esta compra todavía no está conectado:
                    su ruta no está registrada en el backend.
                  </p>
                ) : (
                  <DiagnosticoPago detalle={detalle} />
                )}
              </CollapsibleContent>
            </Collapsible>
          </section>
        </div>

        <SheetFooter className="flex-row justify-end">
          <SheetClose asChild>
            <Button variant="outline" className="min-h-11">
              Cerrar
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

/**
 * DiagnosticoPago - the THIRD level: the order, the attempts, the evidence
 * and the manual operations.
 *
 * The state of an attempt is TEXT: the provider layer never inherits the
 * colour of a verdict (`GOV-02-RB-06`).
 */
function DiagnosticoPago({ detalle }: { detalle: AdminPagoDetalleOut }) {
  return (
    <div className="flex flex-col gap-4">
      <dl className="grid grid-cols-2 gap-3">
        <Dato etiqueta="Orden de pago" valor={detalle.orden_pago_id ?? "—"} />
        <Dato etiqueta="Origen de la evidencia" valor={detalle.origen_pago} />
        <Dato
          etiqueta="Estado de la compra"
          valor={detalle.compra?.estado ?? "—"}
        />
        <Dato
          etiqueta="Total de la compra"
          valor={
            detalle.compra
              ? `${detalle.compra.total} ${detalle.compra.moneda}`
              : "—"
          }
        />
      </dl>

      <div className="flex flex-col gap-2">
        <h4 className="text-sm font-semibold text-foreground">
          Intentos del proveedor
        </h4>
        <ul className="flex list-none flex-col gap-2">
          {detalle.intentos.map((intento) => (
            <li
              key={intento.id}
              className="rounded-[var(--radius-md)] border border-border bg-surface-recessed/60 px-3 py-2 text-sm leading-snug"
            >
              <span className="font-medium text-foreground">
                Intento {intento.intento} · {intento.estado}
              </span>
              <span className="block text-xs text-muted-foreground">
                Verificada: {intento.verificada ? "sí" : "no"} · Respuesta:{" "}
                {intento.codigo_respuesta || "—"} · Método:{" "}
                {intento.metodo_pago || "—"} · Creada: {intento.creada_en}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-sm font-semibold text-foreground">
          Operaciones manuales
        </h4>
        <ul className="flex list-none flex-col gap-2">
          {detalle.operaciones_manuales.map((operacion) => (
            <li
              key={operacion.id}
              className="rounded-[var(--radius-md)] border border-border bg-surface-recessed/60 px-3 py-2 text-sm leading-snug"
            >
              <span className="font-medium text-foreground">
                {operacion.canal} · {operacion.monto} {operacion.moneda}
              </span>
              <span className="block text-xs text-muted-foreground">
                {operacion.motivo} · {operacion.registrada_en} ·{" "}
                {operacion.actor}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/**
 * One fact of the diagnosis, as a term of a definition list.
 */
function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-foreground-muted">{etiqueta}</dt>
      <dd className="text-sm font-medium break-words text-foreground">
        {valor}
      </dd>
    </div>
  );
}
