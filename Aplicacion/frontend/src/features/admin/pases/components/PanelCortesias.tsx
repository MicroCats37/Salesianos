"use client";

import { Gift, RefreshCw, Ticket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AdminDataTable } from "@/features/admin/components/AdminDataTable";
import { AdminEmptyState } from "@/features/admin/components/AdminEmptyState";
import type { EstadoListaCortesias } from "../hooks/useAdminPases";
import type { AdminCortesiaListaItem } from "../schemas/admin.pase.schema";
import {
  cortesiaEsRevocable,
  cortesiaEstadoLabel,
} from "../utils/admin.pase.utils";

/** The format of the instants of the area. */
const FORMATO_FECHA = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "medium",
});

export interface PanelCortesiasProps {
  /** The state of the read of the courtesies. */
  estado: EstadoListaCortesias;
  /** Called when the operator asks for the form of a new courtesy. */
  onRegistrar?: () => void;
  /** Called when the operator asks to revoke ONE courtesy. */
  onRevocar?: (cortesia: AdminCortesiaListaItem) => void;
  /** Called when the operator asks for the credential of ONE courtesy. */
  onEmitirCredencial?: (cortesia: AdminCortesiaListaItem) => void;
  /** Called when the operator asks to read the list again. */
  onReintentar?: () => void;
}

/**
 * PanelCortesias - the administrative list of the courtesies.
 *
 * ## What it shows
 *
 * The ACTAS of the courtesies: who received the entry, which pass was
 * granted, the reason that the acta carries, who granted it and when. The
 * list NEVER shows the token of the management of a purchase nor the detail
 * of a payment.
 *
 * ## What it NEVER shows
 *
 * An amount. A courtesy has no financial facts at all: there is no price,
 * no total and no currency in this panel (`R4`).
 */
export function PanelCortesias({
  estado,
  onRegistrar,
  onRevocar,
  onEmitirCredencial,
  onReintentar,
}: PanelCortesiasProps) {
  if (estado.estado === "cargando") {
    return (
      <output className="block py-10 text-center text-sm text-muted-foreground">
        Cargando las cortesías...
      </output>
    );
  }

  if (estado.estado === "error") {
    return (
      <div className="flex flex-col gap-3">
        <div
          role="alert"
          className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
        >
          {estado.mensaje}
        </div>
        {onReintentar ? (
          <div>
            <Button type="button" variant="outline" onClick={onReintentar}>
              <RefreshCw className="size-4" aria-hidden="true" />
              Reintentar
            </Button>
          </div>
        ) : null}
      </div>
    );
  }

  const cortesias = estado.datos.items;

  if (cortesias.length === 0) {
    return (
      <AdminEmptyState
        icon={Gift}
        title="Todavía no hay cortesías registradas"
        description="Una cortesía es una entrada gratuita de la organización: queda en un acta con su motivo y su responsable, y no genera cobro, orden ni transacción."
        action={
          onRegistrar ? (
            <Button type="button" onClick={onRegistrar}>
              Registrar una cortesía
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {onRegistrar ? (
        <div>
          <Button type="button" onClick={onRegistrar}>
            <Gift className="size-4" aria-hidden="true" />
            Registrar una cortesía
          </Button>
        </div>
      ) : null}

      <AdminDataTable
        caption="Cortesías registradas en la edición"
        columns={[
          { key: "persona", label: "Beneficiaria" },
          { key: "pase", label: "Pase" },
          { key: "estado", label: "Estado" },
          { key: "motivo", label: "Motivo" },
          { key: "actor", label: "Otorgada por" },
          { key: "fecha", label: "Concedida" },
          { key: "acciones", label: "Acciones" },
        ]}
        filas={cortesias.map((cortesia) => ({
          cells: {
            persona: (
              <div className="min-w-48">
                <p className="truncate font-medium text-foreground">
                  {cortesia.persona_nombres}
                </p>
                <p className="text-caption text-muted-foreground">
                  {cortesia.persona_tipo_documento}{" "}
                  {cortesia.persona_numero_documento}
                </p>
              </div>
            ),
            pase: (
              <span className="text-foreground">{cortesia.pase_nombre}</span>
            ),
            estado: cortesiaEstadoLabel(cortesia.estado),
            motivo: (
              <span className="text-caption text-muted-foreground">
                {cortesia.motivo}
              </span>
            ),
            actor: (
              <span className="text-caption text-muted-foreground">
                {cortesia.actor_nombres}
              </span>
            ),
            fecha: (
              <span className="whitespace-nowrap text-caption text-muted-foreground">
                {FORMATO_FECHA.format(new Date(cortesia.concedido_en))}
              </span>
            ),
            acciones: (
              <div className="flex flex-wrap gap-2">
                {onRevocar && cortesiaEsRevocable(cortesia.estado) ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    aria-label={`Revocar la cortesía de ${cortesia.persona_nombres}`}
                    onClick={() => onRevocar(cortesia)}
                  >
                    Revocar
                  </Button>
                ) : null}
                {onEmitirCredencial && cortesia.derecho_id ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    aria-label={`Emitir la credencial de ${cortesia.persona_nombres}`}
                    onClick={() => onEmitirCredencial(cortesia)}
                  >
                    <Ticket className="size-4" aria-hidden="true" />
                    Emitir credencial
                  </Button>
                ) : null}
              </div>
            ),
          },
        }))}
        vacio={null}
      />

      {cortesias.some((cortesia) => !cortesia.derecho_id) ? (
        <p className="text-caption text-muted-foreground">
          La credencial de puerta se emite contra el DERECHO, no contra el acta.
          Estas cortesías no tienen un derecho asociado, así que no pueden
          emitir credencial.
        </p>
      ) : null}
    </div>
  );
}
