"use client";

import { Fingerprint, ShieldQuestion, UserPlus } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useAgregarParticipanteEquipo } from "../hooks/useAsistidoAdmin";
import {
  agregarParticipanteFormSchema,
  type AgregarParticipanteFormData,
} from "../schemas/asistido.schema";

export interface ModalAgregarParticipanteProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal opens or closes. */
  onOpenChange: (open: boolean) => void;
  /** The team the participant joins. */
  equipoId: string;
  /** The name of the team, as the server published it. */
  equipoNombre: string;
  /** Called when the command succeeded and the modal can close. */
  onAgregado?: () => void;
}

const valoresIniciales: AgregarParticipanteFormData = {
  tipo_documento: "DNI",
  numero_documento: "",
  rol: "JUGADOR",
  motivo: "",
};

/**
 * ModalAgregarParticipante - the administrative add of a participant.
 *
 * ## The person is identified by her EXACT DOCUMENT
 *
 * The form asks for the document and NOTHING ELSE about the person: adding a
 * participant never creates a `Persona` and never edits one. If the document
 * is not in the padrón, the backend answers 404 and the modal shows that
 * message verbatim.
 *
 * ## The rules are NOT checked here
 *
 * Capacity, duplicate, discipline and eligibility belong to the backend: the
 * modal never computes them and never hides a command because it "looks
 * wrong".
 */
export function ModalAgregarParticipante({
  open,
  onOpenChange,
  equipoId,
  equipoNombre,
  onAgregado,
}: ModalAgregarParticipanteProps) {
  const agregar = useAgregarParticipanteEquipo();

  return (
    <AppFormModal<AgregarParticipanteFormData>
      open={open}
      onOpenChange={onOpenChange}
      title="Agregar participante al equipo"
      description={`La persona se identifica por su documento exacto y debe estar en el padrón. El equipo "${equipoNombre}" aplica su capacidad, su disciplina y sus reglas de elegibilidad.`}
      eyebrow="Plantilla del equipo"
      icon={<UserPlus className="size-5" aria-hidden="true" />}
      primaryLabel="Agregar al equipo"
      primaryLoadingLabel="Agregando..."
      primaryLoading={agregar.isPending}
      onPrimary={() => undefined}
      schema={agregarParticipanteFormSchema}
      initialData={valoresIniciales}
      onSubmit={async (datos) => {
        await agregar.mutateAsync({
          equipoId,
          payload: {
            tipo_documento: datos.tipo_documento,
            numero_documento: datos.numero_documento,
            rol: datos.rol,
            motivo: datos.motivo,
          },
        });

        onAgregado?.();
      }}
      showErrorsAsToasts
      size="lg"
      bodyClassName="max-h-[70vh] overflow-y-auto"
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <>
          {submissionMessage?.type === "error" ? (
            <p
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
            >
              {submissionMessage.message}
            </p>
          ) : null}
          <CamposParticipante methods={methods} bloqueado={isSubmitting} />
        </>
      )}
    </AppFormModal>
  );
}

/**
 * The fields of the add of a participant.
 *
 * The form is the Mode 1 (`children`): the label, the icon and the error of
 * every field are drawn ONCE by `FormField`. The two selects read their
 * value with `useController`, ACOTADO a su campo: el formulario no se vuelve
 * a dibujar con cada tecla.
 */
function CamposParticipante({
  methods,
  bloqueado,
}: {
  methods: UseFormReturn<AgregarParticipanteFormData>;
  bloqueado: boolean;
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: tipoDocumento } = useController({
    control: controlFormulario,
    name: "tipo_documento",
  });
  const { field: rol } = useController({
    control: controlFormulario,
    name: "rol",
  });

  return (
    <fieldset disabled={bloqueado} className="contents">
      <FormGrid>
        <FormField
          id="participante-tipo-documento"
          label="Tipo de documento"
          required
          icon={Fingerprint}
          span={4}
          error={errors.tipo_documento?.message}
        >
          {(control) => (
            <Select
              value={tipoDocumento.value}
              onValueChange={tipoDocumento.onChange}
            >
              <SelectTrigger
                {...control}
                onBlur={tipoDocumento.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige el tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DNI">DNI</SelectItem>
                <SelectItem value="CE">Carné de extranjería</SelectItem>
                <SelectItem value="PAS">Pasaporte</SelectItem>
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id="participante-numero-documento"
          label="Número de documento"
          required
          icon={Fingerprint}
          span={8}
          helper="Debe coincidir exactamente con el documento registrado."
          error={errors.numero_documento?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("numero_documento")}
              autoFocus
              inputMode="text"
            />
          )}
        </FormField>

        <FormField
          id="participante-rol"
          label="Rol en el equipo"
          required
          icon={ShieldQuestion}
          span={12}
          error={errors.rol?.message}
        >
          {(control) => (
            <Select value={rol.value} onValueChange={rol.onChange}>
              <SelectTrigger
                {...control}
                onBlur={rol.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige el rol" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="JUGADOR">Jugador</SelectItem>
                <SelectItem value="CAPITAN">Capitán</SelectItem>
                <SelectItem value="DELEGADO">Delegado</SelectItem>
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id="participante-motivo"
          label="Motivo"
          required
          span={12}
          helper="Queda registrado en el acta de la acción sensible."
          error={errors.motivo?.message}
        >
          {(control) => (
            <Textarea {...control} {...register("motivo")} rows={3} />
          )}
        </FormField>
      </FormGrid>
    </fieldset>
  );
}
