"use client";

import { Receipt } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import type {
  CompraInscripcion,
  ComprasInscripcion,
} from "../types/inscripcion.types";

export interface PanelComprasProps {
  /** The purchases of the registration, as the server published them. */
  compras: ComprasInscripcion | null;
}

function Compra(props: { etiqueta: string; compra: CompraInscripcion }) {
  const compra = props.compra;

  return (
    <li className="flex flex-col gap-1 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4">
      <span className="text-sm font-semibold text-foreground">
        {props.etiqueta}
      </span>
      <span className="text-caption text-muted-foreground">
        Estado: {compra.estado}
      </span>
      <span className="text-caption text-muted-foreground">
        Total: {compra.total} {compra.moneda}
      </span>
      {compra.reutilizada ? (
        <span className="text-caption text-muted-foreground">
          Es la compra pendiente que ya existía: no se creó otra.
        </span>
      ) : null}
    </li>
  );
}

/**
 * PanelCompras - the purchases that finance a registration.
 *
 * The initial purchase comes with the alta and every expansion comes with
 * its own answer (RT-CM-01). The target backend does NOT publish a route
 * that LISTS them, so the list is assembled from the answers it gives and
 * not from an invented endpoint. While that route does not exist the section
 * says so: an empty list would read as "this registration has no purchases",
 * and it HAS one.
 *
 * The amount is printed exactly as the server sends it: the frontend never
 * sums, converts or formats money.
 */
export function PanelCompras(props: PanelComprasProps) {
  const compras = props.compras;

  if (!compras || (!compras.inicial && compras.expansiones.length === 0)) {
    return (
      <RouteEmptyState
        icon={Receipt}
        title="El servidor todavía no publica las compras de una inscripción"
        description="La compra de los cupos iniciales se abre al crear la inscripción y cada ampliación llega con su propia respuesta. En cuanto exista un listado, aquí aparecerán con su estado y su total."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {compras.inicial ? (
        <Compra etiqueta="Compra inicial" compra={compras.inicial} />
      ) : null}

      {compras.expansiones.map((expansion) => (
        <Compra
          key={expansion.compra_id}
          etiqueta="Ampliación de cupos"
          compra={expansion}
        />
      ))}
    </ul>
  );
}
