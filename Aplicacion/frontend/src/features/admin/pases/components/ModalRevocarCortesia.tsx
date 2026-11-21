"use client";

import { Ban, ScrollText } from "lucide-react";
import { useState } from "react";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useRevocarCortesia } from "../hooks/useAdminPases";
import {
  type AdminCortesiaListaItem,
  type RevocarCortesiaFormData,
  revocarCortesiaFormSchema,
} from "../schemas/admin.pase.schema";
import { type EstadoDeFallo, estadoDeFallo } from "../utils/admin.pase.utils";
import { AvisoFalloPase } from "./AvisoFalloPase";

export interface ModalRevocarCortesiaProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal opens or closes. */
  onOpenChange: (open: boolean) => void;
  /** The courtesy that is going to be revoked. */
  cortesia: AdminCortesiaListaItem | null;
  /** Called when the command succeeded and the modal can close. */
  onRevocada?: () => void;
}

/**
 * ModalRevocarCortesia - the revocation of a courtesy.
 *
 * ## WHAT IT DOES
 *
 * It revokes the RIGHT of the person and marks the acta as revoked. The
 * revocation is PERMANENT and AUDITED: the reason is mandatory and it stays
 * in the acta.
 *
 * ## WHAT IT NEVER DOES
 *
 * It never touches the money: a courtesy has no purchase, no payment order
 * and no transaction to reverse (`R4`).
 */
export function ModalRevocarCortesia({
  open,
  onOpenChange,
  cortesia,
  onRevocada,
}: ModalRevocarCortesiaProps) {
  const revocar = useRevocarCortesia();
  const [fallo, setFallo] = useState<EstadoDeFallo | null>(null);

  return (
    <AppFormModal<RevocarCortesiaFormData>
      open={open}
      onOpenChange={(siguiente) => {
        if (!siguiente) {
          setFallo(null);
        }
        onOpenChange(siguiente);
      }}
      title="Revocar la cortesía"
      description="La revocación es permanente y queda auditada con su motivo. No revierte ningún cobro, porque una cortesía no tiene ninguno."
      eyebrow="Cortesías"
      icon={<Ban className="size-5" aria-hidden="true" />}
      primaryLabel="Revocar la cortesía"
      primaryLoadingLabel="Revocando..."
      primaryLoading={revocar.isPending}
      primaryDisabled={!cortesia}
      onPrimary={() => undefined}
      schema={revocarCortesiaFormSchema}
      initialData={{ motivo: "" }}
      onSubmit={async (datos) => {
        setFallo(null);

        if (!cortesia) {
          const mensaje = "No hay ninguna cortesía seleccionada.";
          setFallo({
            tipo: "validacion",
            titulo: "No hay nada que revocar",
            mensaje,
          });
          throw new Error(mensaje);
        }

        try {
          await revocar.mutateAsync({
            cortesiaId: cortesia.id,
            payload: { motivo: datos.motivo },
          });

          onRevocada?.();
        } catch (error) {
          setFallo(estadoDeFallo(error));
          throw error;
        }
      }}
      size="lg"
      bodyClassName="max-h-[70vh] overflow-y-auto"
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <>
          {fallo ? <AvisoFalloPase fallo={fallo} /> : null}

          {!fallo && submissionMessage?.type === "error" ? (
            <p
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
            >
              {submissionMessage.message}
            </p>
          ) : null}

          {cortesia ? (
            <section
              aria-labelledby="revocar-cortesia-resumen"
              className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border p-4"
            >
              <h3
                id="revocar-cortesia-resumen"
                className="text-sm font-semibold text-foreground"
              >
                La cortesía que se revoca
              </h3>
              <p className="text-sm text-foreground">
                {cortesia.persona_nombres} — {cortesia.pase_nombre}
              </p>
              <p className="text-caption text-muted-foreground">
                {cortesia.persona_tipo_documento}{" "}
                {cortesia.persona_numero_documento}
              </p>
              <p className="text-caption text-muted-foreground">
                Motivo del otorgamiento: {cortesia.motivo}
              </p>
            </section>
          ) : null}

          <fieldset disabled={isSubmitting} className="contents">
            <FormGrid>
              <FormField
                id="cortesia-revocar-motivo"
                label="Motivo de la revocación"
                required
                icon={ScrollText}
                span={12}
                helper="Queda en el acta, con tu nombre y la fecha. Sin motivo no hay auditoría."
                error={methods.formState.errors.motivo?.message}
              >
                {(control) => (
                  <Textarea
                    {...control}
                    {...methods.register("motivo")}
                    rows={3}
                  />
                )}
              </FormField>
            </FormGrid>
          </fieldset>
        </>
      )}
    </AppFormModal>
  );
}
