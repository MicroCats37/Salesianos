"use client";

import { ShieldQuestion, UserPlus } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useAgregarParticipanteEquipo } from "../hooks/useAsistidoAdmin";
import {
  type AgregarParticipanteFormData,
  agregarParticipanteFormSchema,
} from "../schemas/asistido.schema";
import { BloqueIdentidadAdministrativa } from "./BloqueIdentidadAdministrativa";

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
  nombres: "",
  apellidos: "",
  genero: "",
  estado_identidad: "SIN_CONSULTAR",
  rol: "JUGADOR",
  motivo: "Alta administrativa de participante en el equipo.",
};

/**
 * ModalAgregarParticipante - the administrative add of a participant.
 *
 * ## The person is identified by her EXACT DOCUMENT
 *
 * The IDENTITY BLOCK resolves the document: if the padrón already has that
 * person, her identity is REUSED and her names are not editable; if it does
 * not have her, the block reveals the names, the surname and the gender and
 * the command REGISTERS her —as a civil identity, NEVER as an account.
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
      description={`La identidad se resuelve por su documento exacto: el padrón manda y, si la persona no está, se registra sin cuenta. El equipo "${equipoNombre}" aplica su capacidad, su disciplina y sus reglas de elegibilidad.`}
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
            nombres: datos.nombres,
            apellidos: datos.apellidos,
            genero: datos.genero,
            rol: datos.rol,
            motivo: datos.motivo,
          },
        });

        onAgregado?.();
      }}
      showErrorsAsToasts
      size="md"
      bodyClassName="max-h-[65vh] overflow-y-auto"
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
 * every field are drawn ONCE by `FormField`. The identity lives in the
 * SHARED BLOCK, so the three administrative forms resolve a document the same
 * way. The select reads its value with `useController`, ACOTADO a su campo:
 * el formulario no se vuelve a dibujar con cada tecla.
 */
function CamposParticipante({
  methods,
  bloqueado,
}: {
  methods: UseFormReturn<AgregarParticipanteFormData>;
  bloqueado: boolean;
}) {
  const {
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: rol } = useController({
    control: controlFormulario,
    name: "rol",
  });

  return (
    <fieldset disabled={bloqueado} className="contents">
      <FormGrid>
        <BloqueIdentidadAdministrativa
          idPrefijo="participante"
          bloqueado={bloqueado}
          permiteCorreccionGenero
        />

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
                id={control.id}
                aria-invalid={control["aria-invalid"]}
                aria-describedby={control["aria-describedby"]}
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
      </FormGrid>
    </fieldset>
  );
}
