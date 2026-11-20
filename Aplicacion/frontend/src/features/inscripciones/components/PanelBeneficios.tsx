"use client";

import { Gift } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import type { BeneficioConcedido } from "../types/inscripcion.types";

export interface PanelBeneficiosProps {
  /**
   * The benefits granted to the registration.
   *
   * `null` means that the server does not publish them yet: the domain has
   * the record (`BeneficioConcedido`) but no presenter exposes it, so the
   * section says so instead of showing the benefits of the catalogue as if
   * they had been granted.
   */
  beneficios: readonly BeneficioConcedido[] | null;
}

/**
 * PanelBeneficios - the benefits granted to a registration.
 *
 * The benefits of the CATALOGUE (what the package offers) and the benefits
 * GRANTED (what this registration has) are two different things and they
 * are never mixed: the first is a product, the second is a fact.
 *
 * While the backend does not publish the granted ones, the section is
 * honest about it.
 */
export function PanelBeneficios(props: PanelBeneficiosProps) {
  const beneficios = props.beneficios;

  if (!beneficios || beneficios.length === 0) {
    return (
      <RouteEmptyState
        icon={Gift}
        title="Los beneficios concedidos todavía no se publican"
        description="El servidor registra qué beneficios se otorgan a cada inscripción, pero todavía no expone esa lista. Los beneficios que ofrece el paquete son otra cosa: se ven al elegirlo."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {beneficios.map((beneficio) => (
        <li
          key={beneficio.codigo}
          className="flex flex-col gap-1 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
        >
          <span className="text-sm font-semibold text-foreground">
            {beneficio.nombre}
          </span>
          <span className="text-caption text-muted-foreground">
            Tipo: {beneficio.tipo}
          </span>
          <span className="text-caption text-muted-foreground">
            Cantidad: {beneficio.cantidad}
          </span>
        </li>
      ))}
    </ul>
  );
}
