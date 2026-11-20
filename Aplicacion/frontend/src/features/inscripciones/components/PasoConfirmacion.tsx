"use client";

import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type {
  CotizacionPaquete,
  PaqueteCatalogo,
  PromocionCatalogo,
} from "../types/inscripcion.types";

export interface PasoConfirmacionProps {
  /** The chosen package, exactly as the catalogue publishes it. */
  paquete: PaqueteCatalogo | null;
  /** The cohort that the visitor selected explicitly. */
  promocion: PromocionCatalogo | null;
  /** The number of people that the registration buys. */
  cantidad: number;
  /** The last quotation of the server, when it already arrived. */
  cotizacion: CotizacionPaquete | null;
}

/**
 * PasoConfirmacion - the last step of the wizard.
 *
 * It names the EFFECT of the action, because the action creates a
 * registration and opens a pending purchase (S-10, SH-03 section 1).
 *
 * The wording is the one of the domain: an unpaid purchase NEVER grants a
 * cup (RN-I02, QA-I01), so the confirmation says that the cupos are enabled
 * when the payment is confirmed and not before.
 *
 * It does not ask for a card: the payment happens in the checkout of the
 * commerce module, which this packet does not own.
 */
export function PasoConfirmacion(props: PasoConfirmacionProps) {
  const paquete = props.paquete;
  const promocion = props.promocion;
  const cantidad = props.cantidad;
  const cotizacion = props.cotizacion;

  /**
   * The consequences of the action, in order.
   *
   * They are declared as OBJECTS with a stable key so that the list never
   * leans on the index of an array, and so that the wording of each one is
   * a single place of the file.
   */
  const consecuencias = [
    {
      clave: "inscripcion",
      texto:
        "Se registra tu inscripción" +
        (paquete ? ` para el paquete ${paquete.nombre}` : "") +
        " con " +
        (cantidad === 1 ? "1 persona" : `${cantidad} personas`) +
        " y " +
        (promocion
          ? `la promoción ${promocion.nombre}`
          : "la promoción elegida") +
        " con los equipos que declaraste.",
    },
    {
      clave: "compra",
      texto:
        "Se abre una compra pendiente con el precio del catálogo" +
        (cotizacion ? ` (${cotizacion.total} ${cotizacion.moneda})` : "") +
        ". Todavía no se cobra nada.",
    },
    {
      clave: "cupos",
      texto:
        "El servidor asigna a cada equipo la categoría que corresponde a tu " +
        "promoción, y cuando el pago se confirme los cupos se habilitan y ya " +
        "puedes asignar las personas a los equipos.",
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <ShieldCheck className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-section-title text-foreground">
          Qué pasa al confirmar
        </h3>
        {/*
         * The quoted total is the figure that the visitor came for, and it is
         * the answer of the SERVER: it is printed as it arrived and it is
         * never recomputed here.
         */}
        {cotizacion ? (
          <Badge
            variant="outline"
            className="border-info/45 bg-info/10 font-bold tracking-wide text-info"
          >
            Cotiza {cotizacion.total} {cotizacion.moneda}
          </Badge>
        ) : null}
      </div>

      <ol className="flex flex-col gap-3">
        {consecuencias.map((consecuencia, indice) => (
          <li
            key={consecuencia.clave}
            className="group flex gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3 transition-colors duration-(--motion-duration-fast) hover:border-border-strong"
          >
            <span className="flex flex-col items-center gap-1">
              <span
                aria-hidden="true"
                className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-accent-foreground shadow-[var(--elevation-sm)]"
              >
                {indice + 1}
              </span>
              {indice < consecuencias.length - 1 ? (
                <span
                  aria-hidden="true"
                  className="h-full w-px flex-1 bg-border"
                />
              ) : null}
            </span>
            <span className="text-sm leading-relaxed text-foreground">
              {consecuencia.texto}
            </span>
          </li>
        ))}
      </ol>

      <p className="text-caption text-muted-foreground">
        Si ya existía una inscripción para este paquete, el servidor devuelve
        esa misma inscripción y su compra pendiente: no se crea una segunda ni
        se cobra dos veces.
      </p>
    </div>
  );
}
