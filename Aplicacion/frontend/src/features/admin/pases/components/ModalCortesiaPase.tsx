"use client";

import { Gift, ScrollText, Ticket } from "lucide-react";
import { useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { BloqueIdentidadAdministrativa } from "@/features/admin/asistido/components/BloqueIdentidadAdministrativa";
import { useCatalogoPases } from "@/features/pases/hooks/useCatalogoPases";
import type { PaseCatalogo } from "@/features/pases/schemas/pase.schema";
import { useOtorgarCortesia } from "../hooks/useAdminPases";
import {
  type AdminCortesia,
  type CortesiaPaseFormData,
  cortesiaPaseFormSchema,
} from "../schemas/admin.pase.schema";
import { type EstadoDeFallo, estadoDeFallo } from "../utils/admin.pase.utils";
import { AvisoFalloPase } from "./AvisoFalloPase";

export interface ModalCortesiaPaseProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal opens or closes. */
  onOpenChange: (open: boolean) => void;
  /** Called when the command succeeded and the modal can close. */
  onOtorgada?: (cortesia: AdminCortesia) => void;
}

/** The values the form starts with. */
const VALORES_INICIALES: CortesiaPaseFormData = {
  tipo_documento: "DNI",
  numero_documento: "",
  nombres: "",
  apellidos: "",
  genero: "",
  estado_identidad: "SIN_CONSULTAR",
  pase_id: "",
  motivo: "",
  confirma_sin_cobro: false,
};

/**
 * ModalCortesiaPase - the grant of a courtesy.
 *
 * ## WHAT IT IS
 *
 * A courtesy is an entry that the organization GIVES: it has NO financial
 * facts at all. There is no price, no total and no currency in this form,
 * and the browser never computes an amount (`R4`).
 *
 * ## THE CONFIRMATION
 *
 * The operator says it EXPLICITLY: the checkbox states that the command does
 * not create a purchase, a payment order, a transaction nor a balance. It is
 * a required field, not a decoration.
 *
 * ## THE IDENTITY
 *
 * The identity is resolved by the SHARED administrative block, imported and
 * never modified: the same document, the same padrón and the same three
 * states as the participant and the assisted purchase.
 */
export function ModalCortesiaPase({
  open,
  onOpenChange,
  onOtorgada,
}: ModalCortesiaPaseProps) {
  const otorgar = useOtorgarCortesia();
  const catalogo = useCatalogoPases();
  const [fallo, setFallo] = useState<EstadoDeFallo | null>(null);

  const pases = catalogo.data?.pases ?? [];
  const edicionNombre = catalogo.data?.edicion_nombre;

  return (
    <AppFormModal<CortesiaPaseFormData>
      open={open}
      onOpenChange={(siguiente) => {
        if (!siguiente) {
          setFallo(null);
        }
        onOpenChange(siguiente);
      }}
      title="Registrar una cortesía"
      description="La entrada se otorga sin cobro: queda en un acta con su motivo, su responsable y la fecha, y habilita el ingreso en la puerta con una credencial."
      eyebrow="Cortesías"
      icon={<Gift className="size-5" aria-hidden="true" />}
      primaryLabel="Registrar la cortesía"
      primaryLoadingLabel="Registrando..."
      primaryLoading={otorgar.isPending}
      primaryDisabled={
        catalogo.isPending || catalogo.isError || pases.length === 0
      }
      onPrimary={() => undefined}
      schema={cortesiaPaseFormSchema}
      initialData={VALORES_INICIALES}
      onSubmit={async (datos) => {
        setFallo(null);

        const pase = pases.find((candidato) => candidato.id === datos.pase_id);

        if (!pase) {
          setFallo({
            tipo: "validacion",
            titulo: "Elige el pase que se otorga",
            mensaje: "El pase elegido no está en el catálogo vigente.",
          });
          throw new Error("El pase elegido no está en el catálogo vigente.");
        }

        try {
          const resultado = await otorgar.mutateAsync({
            edicion_id: pase.edicion_id,
            pase_id: pase.id,
            tipo_documento: datos.tipo_documento,
            numero_documento: datos.numero_documento,
            nombres: datos.nombres,
            apellidos: datos.apellidos,
            motivo: datos.motivo,
          });

          onOtorgada?.(resultado);
        } catch (error) {
          setFallo(estadoDeFallo(error));
          throw error;
        }
      }}
      size="xl"
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

          {catalogo.isError ? (
            <p
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
            >
              No pudimos cargar el catálogo de pases: no se puede otorgar una
              cortesía sin saber qué pase se otorga.
            </p>
          ) : null}

          <CamposCortesia
            methods={methods}
            bloqueado={isSubmitting}
            pases={pases}
            edicionNombre={edicionNombre}
          />
        </>
      )}
    </AppFormModal>
  );
}

/**
 * The fields of the grant of a courtesy.
 *
 * The form is the Mode 1 (`children`): the label, the icon and the error of
 * every field are drawn ONCE by `FormField`. The IDENTITY lives in the
 * SHARED BLOCK, so the courtesy resolves a document the same way as the
 * participant and the assisted purchase.
 */
function CamposCortesia({
  methods,
  bloqueado,
  pases,
  edicionNombre,
}: {
  methods: UseFormReturn<CortesiaPaseFormData>;
  bloqueado: boolean;
  pases: PaseCatalogo[];
  edicionNombre?: string;
}) {
  const {
    register,
    control,
    formState: { errors },
  } = methods;

  const { field: pase } = useController({
    control,
    name: "pase_id",
  });

  const { field: confirmacion } = useController({
    control,
    name: "confirma_sin_cobro",
  });

  return (
    <fieldset disabled={bloqueado} className="contents">
      <section
        aria-labelledby="cortesia-pase-titulo"
        className="flex flex-col gap-3"
      >
        <h3
          id="cortesia-pase-titulo"
          className="text-sm font-semibold text-foreground"
        >
          El pase que se otorga
        </h3>

        <FormGrid>
          <FormField
            id="cortesia-pase"
            label="Pase"
            required
            icon={Ticket}
            span={12}
            helper={
              edicionNombre
                ? `Edición ${edicionNombre}. El pase se toma del catálogo vigente.`
                : "El pase se toma del catálogo vigente."
            }
            error={errors.pase_id?.message}
          >
            {(control) => (
              <Select value={pase.value} onValueChange={pase.onChange}>
                <SelectTrigger
                  id={control.id}
                  aria-invalid={control["aria-invalid"]}
                  aria-describedby={control["aria-describedby"]}
                  onBlur={pase.onBlur}
                  className="w-full"
                >
                  <SelectValue placeholder="Elige el pase que se otorga" />
                </SelectTrigger>
                <SelectContent>
                  {pases.map((candidato) => (
                    <SelectItem key={candidato.id} value={candidato.id}>
                      {candidato.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </FormField>
        </FormGrid>
      </section>

      <section
        aria-labelledby="cortesia-identidad-titulo"
        className="flex flex-col gap-3"
      >
        <h3
          id="cortesia-identidad-titulo"
          className="text-sm font-semibold text-foreground"
        >
          Quién recibe la entrada
        </h3>

        <BloqueIdentidadAdministrativa
          idPrefijo="cortesia"
          bloqueado={bloqueado}
        />
      </section>

      <section
        aria-labelledby="cortesia-motivo-titulo"
        className="flex flex-col gap-3"
      >
        <h3
          id="cortesia-motivo-titulo"
          className="text-sm font-semibold text-foreground"
        >
          Motivo y confirmación
        </h3>

        <FormGrid>
          <FormField
            id="cortesia-motivo"
            label="Motivo"
            required
            icon={ScrollText}
            span={12}
            helper="Queda en el acta de la cortesía, con tu nombre y la fecha."
            error={errors.motivo?.message}
          >
            {(control) => (
              <Textarea {...control} {...register("motivo")} rows={3} />
            )}
          </FormField>
        </FormGrid>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-start gap-2">
            <Checkbox
              id="cortesia-confirmacion"
              checked={confirmacion.value === true}
              onCheckedChange={(valor) => confirmacion.onChange(valor === true)}
              onBlur={confirmacion.onBlur}
              aria-invalid={errors.confirma_sin_cobro ? true : undefined}
              aria-describedby={
                errors.confirma_sin_cobro
                  ? "cortesia-confirmacion-error"
                  : "cortesia-confirmacion-helper"
              }
            />
            <Label
              htmlFor="cortesia-confirmacion"
              className="text-sm font-medium leading-snug text-foreground"
            >
              Confirmo que esta cortesía no genera cobro: no crea compra, orden
              de pago, transacción ni saldo.
            </Label>
          </div>

          {errors.confirma_sin_cobro ? (
            <p
              id="cortesia-confirmacion-error"
              role="alert"
              className="text-caption text-destructive"
            >
              {errors.confirma_sin_cobro.message}
            </p>
          ) : (
            <p
              id="cortesia-confirmacion-helper"
              className="text-caption text-muted-foreground"
            >
              Sin la confirmación, el comando no se envía.
            </p>
          )}
        </div>
      </section>
    </fieldset>
  );
}
