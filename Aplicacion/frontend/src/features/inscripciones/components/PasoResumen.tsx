"use client";

import { Package, Receipt, Users } from "lucide-react";
import type { EquipoAltaFormData } from "../schemas/alta-inscripcion.schema";
import type { PaqueteCatalogo } from "../types/inscripcion.types";

export interface PasoResumenProps {
  /** The chosen package, exactly as the catalogue publishes it. */
  paquete: PaqueteCatalogo | null;
  /** The teams the visitor declared in the previous step. */
  equipos: readonly EquipoAltaFormData[];
}

function Fila(props: {
  termino: string;
  valor: string;
  detalle?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5 border-t border-border py-2.5 first:border-t-0 first:pt-0">
      <dt className="text-caption text-muted-foreground">{props.termino}</dt>
      <dd className="text-sm font-semibold text-foreground">{props.valor}</dd>
      {props.detalle ? (
        <dd className="text-caption text-muted-foreground">{props.detalle}</dd>
      ) : null}
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
 */
export function PasoResumen(props: PasoResumenProps) {
  const paquete = props.paquete;
  const equipos = props.equipos;

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

      <dl className="rounded-[var(--radius-lg)] border border-border bg-surface-raised px-4 py-3">
        <Fila termino="Paquete" valor={paquete.nombre} />

        <Fila
          termino="Equipos"
          valor={equipos.length === 1 ? "1 equipo" : equipos.length + " equipos"}
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
              : paquete.cupos_incluidos + " cupos"
          }
          detalle="Se habilitan cuando el pago se confirme. Antes de eso, la inscripción no tiene ningún cupo disponible."
        />

        <Fila
          termino="Precio del catálogo"
          valor={paquete.precio.monto + " " + paquete.precio.moneda}
          detalle="El servidor lo vuelve a resolver contra la edición vigente al confirmar."
        />

        {disciplinas ? (
          <Fila termino="Disciplinas del paquete" valor={disciplinas} />
        ) : null}
      </dl>

      <p className="flex items-start gap-2 text-caption text-muted-foreground">
        <Package className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
        La promoción y los titulares de cada equipo los registra el comité
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
