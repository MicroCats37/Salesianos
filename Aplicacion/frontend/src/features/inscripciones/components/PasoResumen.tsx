"use client";

import { Package, Receipt, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { EquipoAltaFormData } from "../schemas/alta-inscripcion.schema";
import type {
  CotizacionPaquete,
  PaqueteCatalogo,
  PromocionCatalogo,
} from "../types/inscripcion.types";

export interface PasoResumenProps {
  /** The chosen package, exactly as the catalogue publishes it. */
  paquete: PaqueteCatalogo | null;
  /** The teams the visitor declared in the previous step. */
  equipos: readonly EquipoAltaFormData[];
  /** The cohort that the visitor selected explicitly. */
  promocion: PromocionCatalogo | null;
  /** The secondary cohort of a fused registration, when there is one. */
  fusionPromocion: PromocionCatalogo | null;
  /** The number of people that the registration buys. */
  cantidad: number;
  /** The last quotation of the server, when it already arrived. */
  cotizacion: CotizacionPaquete | null;
}

/**
 * One row of the review.
 *
 * From 640 the term becomes a column and the answer becomes the second one:
 * the visitor reads a TABLE of facts instead of a stack of paragraphs, and
 * the detail of the row stays under the value that it explains.
 */
function Fila(props: { termino: string; valor: string; detalle?: string }) {
  return (
    <div className="grid gap-0.5 border-t border-border py-3 first:border-t-0 first:pt-0 sm:grid-cols-[minmax(0,13rem)_minmax(0,1fr)] sm:gap-4">
      <dt className="text-caption text-muted-foreground">{props.termino}</dt>
      <dd className="flex flex-col gap-0.5">
        <span className="text-sm font-semibold text-foreground">
          {props.valor}
        </span>
        {props.detalle ? (
          <span className="text-caption text-muted-foreground">
            {props.detalle}
          </span>
        ) : null}
      </dd>
    </div>
  );
}

/**
 * PasoResumen - the third step of the wizard.
 *
 * It is a REVIEW, not an input: nothing is decided here. Every figure comes
 * from the catalogue of the edition, printed exactly as the server sends it.
 *
 * The wording of the cupos is deliberate: the package DECLARES how many
 * cupos it grants, and the server enables them when the payment is
 * confirmed (RN-I02, QA-I01). The summary never says that they are
 * available.
 *
 * The category of the teams is NOT printed: it is a SERVER-DERIVED fact
 * that arrives with the registration, and the summary does not guess it
 * from the cohort (`RN-C02`, `QA-K01`).
 */
export function PasoResumen(props: PasoResumenProps) {
  const paquete = props.paquete;
  const equipos = props.equipos;
  const promocion = props.promocion;
  const fusionPromocion = props.fusionPromocion;
  const cantidad = props.cantidad;
  const cotizacion = props.cotizacion;

  if (!paquete) {
    return (
      <p className="text-sm text-muted-foreground">
        Elige un paquete para ver el resumen de lo que se va a registrar.
      </p>
    );
  }

  const disciplinas = paquete.disciplinas
    .map((disciplina) => disciplina.nombre)
    .join(", ");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Receipt className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-section-title text-foreground">
          Lo que vas a registrar
        </h3>
      </div>

      {/*
       * The total is the HERO of the summary: it is the figure the visitor
       * came for. It is the answer of the server, printed as it arrived,
       * with the rule of the brand on top of the block.
       */}
      {cotizacion ? (
        <div className="relative overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface-elevated p-4 shadow-[var(--elevation-sm)]">
          <span
            aria-hidden="true"
            className="rule-gold absolute inset-x-0 top-0 h-1"
          />

          <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
            <div className="flex flex-col gap-1">
              <span className="flex flex-wrap items-center gap-2">
                <span className="text-eyebrow-brand text-primary">
                  Total cotizado
                </span>
                {/*
                 * The state of the quotation is the one of the SERVER: it is
                 * printed as it arrived and never translated into a verdict
                 * that the browser would have to decide.
                 */}
                <Badge
                  variant="outline"
                  className="border-info/45 bg-info/10 font-bold tracking-wide text-info"
                >
                  {cotizacion.estado}
                </Badge>
              </span>
              <span className="text-3xl font-bold tabular-nums text-foreground">
                {cotizacion.total} {cotizacion.moneda}
              </span>
            </div>

            <p className="text-caption text-muted-foreground">
              {cotizacion.precio_unitario} {cotizacion.moneda} por persona ·{" "}
              {cotizacion.cantidad_cotizada}{" "}
              {cotizacion.cantidad_cotizada === 1 ? "persona" : "personas"}
            </p>
          </div>
        </div>
      ) : null}

      <dl className="rounded-[var(--radius-lg)] border border-border bg-surface-raised px-4 py-3">
        <Fila termino="Paquete" valor={paquete.nombre} />

        <Fila
          termino="Personas que se anotan"
          valor={cantidad === 1 ? "1 persona" : `${cantidad} personas`}
          detalle={`El mínimo del paquete es ${paquete.minimo_compra_inicial} personas. El precio de cada cupo lo resuelve el servidor contra el catálogo vigente.`}
        />

        <Fila
          termino="Promoción"
          valor={
            promocion ? `${promocion.nombre} · ${promocion.anio}` : "Sin elegir"
          }
          detalle={
            fusionPromocion
              ? `Promoción fusionada: ${fusionPromocion.nombre} · ${fusionPromocion.anio}. Es un dato descriptivo y no cambia la categoría.`
              : "La categoría de cada equipo la deriva el servidor con esta promoción."
          }
        />

        <Fila
          termino="Equipos"
          valor={
            equipos.length === 1 ? "1 equipo" : `${equipos.length} equipos`
          }
          detalle={
            equipos.length === 0
              ? "Todavía no has declarado ningún equipo."
              : undefined
          }
        />

        <Fila
          termino="Cupos que otorga el paquete"
          valor={
            paquete.cupos_incluidos === 1
              ? "1 cupo"
              : `${paquete.cupos_incluidos} cupos`
          }
          detalle="Se habilitan cuando el pago se confirme. Antes de eso, la inscripción no tiene ningún cupo disponible."
        />

        <Fila
          termino="Precio del catálogo"
          valor={`${paquete.precio.monto} ${paquete.precio.moneda}`}
          detalle="El servidor lo vuelve a resolver contra la edición vigente al confirmar."
        />

        {disciplinas ? (
          <Fila termino="Disciplinas del paquete" valor={disciplinas} />
        ) : null}
      </dl>

      <p className="flex items-start gap-2 text-caption text-muted-foreground">
        <Package className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
        La categoría de cada equipo y los titulares los registra el comité
        cuando valida la nómina. Esta pantalla no los calcula.
      </p>

      <p className="flex items-start gap-2 text-caption text-muted-foreground">
        <Users className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
        Puedes asignar las personas a los equipos después de que el pago se
        confirme. El comité validará cada alta.
      </p>
    </div>
  );
}
