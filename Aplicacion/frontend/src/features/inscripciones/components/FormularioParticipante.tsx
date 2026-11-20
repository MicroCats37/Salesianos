"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Hash, TriangleAlert, UserPlus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormFooter } from "@/components/forms/FormFooter";
import { FormGrid } from "@/components/forms/FormGrid";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { handleApiError } from "@/errors";
import { useAgregarParticipante } from "../hooks";
import {
  type FormularioParticipanteFormData,
  FormularioParticipanteSchema,
  ROLES_PARTICIPANTE,
  TIPOS_DOCUMENTO,
} from "../schemas/participante.schema";
import type { EquipoInscripcion } from "../types/inscripcion.types";
import { construirPayloadParticipante } from "../utils/inscripcion.payloads.utils";

export interface FormularioParticipanteProps {
  /** The registration that owns the pool. */
  inscripcionId: string;
  /** The teams of the registration: the destination of the person. */
  equipos: readonly EquipoInscripcion[];
}

const VALORES_INICIALES: FormularioParticipanteFormData = {
  tipo_documento: "DNI",
  numero_documento: "",
  equipo_id: "",
  rol: "JUGADOR",
};

/**
 * FormularioParticipante - the assignment of a person to a team.
 *
 * The person travels by DOCUMENT and the SERVER resolves her from the
 * register (`RT-IN-05`): the browser does not resolve people and does not
 * invent identifiers.
 *
 * The answer of the server is the UPDATED pool, so the balance on the screen
 * is the one of the server and never a number computed here (`RN-I03`).
 *
 * The 422 of the server reaches the control that owns the field: the field
 * errors travel in the raw answer and the form marks each control ONCE.
 */
export function FormularioParticipante(props: FormularioParticipanteProps) {
  const equipos = props.equipos;
  const agregar = useAgregarParticipante();

  const [mensaje, setMensaje] = useState<string | null>(null);

  const methods = useForm<FormularioParticipanteFormData>({
    resolver: zodResolver(FormularioParticipanteSchema),
    defaultValues: VALORES_INICIALES,
  });

  const errores = methods.formState.errors;

  async function alEnviar(datos: FormularioParticipanteFormData) {
    setMensaje(null);

    try {
      await agregar.mutateAsync({
        inscripcion_id: props.inscripcionId,
        payload: construirPayloadParticipante({
          tipo_documento: datos.tipo_documento,
          numero_documento: datos.numero_documento,
          equipo_id: datos.equipo_id,
          rol: datos.rol,
        }),
      });

      methods.reset(VALORES_INICIALES);
    } catch (error) {
      const apiError = handleApiError(error);
      setMensaje(apiError.message);

      if (apiError.fieldErrors) {
        for (const [campo, texto] of Object.entries(apiError.fieldErrors)) {
          methods.setError(campo as keyof FormularioParticipanteFormData, {
            message: texto,
          });
        }
      }
    }
  }

  const idTipo = "participante-tipo-documento";
  const idNumero = "participante-numero-documento";
  const idEquipo = "participante-equipo";
  const idRol = "participante-rol";

  const errorTipo = errores.tipo_documento?.message;
  const errorNumero = errores.numero_documento?.message;
  const errorEquipo = errores.equipo_id?.message;
  const errorRol = errores.rol?.message;

  return (
    <form
      className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
      onSubmit={methods.handleSubmit(alEnviar)}
      noValidate
    >
      <div className="flex items-center gap-2">
        <UserPlus className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-section-title text-foreground">
          Asignar una persona al equipo
        </h3>
      </div>

      <p className="text-caption text-muted-foreground">
        La persona se resuelve en el padrón a partir de su documento. El cupo lo
        asigna el servidor: sólo una persona ocupa un cupo.
      </p>

      <FormGrid>
        <FormField
          id={idTipo}
          label="Tipo de documento"
          required
          span={6}
          error={errorTipo}
        >
          {(control) => (
            <select
              {...control}
              className="min-h-11 w-full rounded-[var(--radius-md)] border border-input bg-transparent px-3 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 aria-invalid:border-destructive"
              {...methods.register("tipo_documento")}
            >
              {TIPOS_DOCUMENTO.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {tipo}
                </option>
              ))}
            </select>
          )}
        </FormField>

        <FormField
          id={idNumero}
          label="Número de documento"
          required
          icon={Hash}
          span={6}
          error={errorNumero}
        >
          {(control) => (
            <Input
              {...control}
              type="text"
              inputMode="numeric"
              autoComplete="off"
              placeholder="Por ejemplo, 12345678"
              {...methods.register("numero_documento")}
            />
          )}
        </FormField>

        <FormField
          id={idEquipo}
          label="Equipo"
          required
          span={6}
          error={errorEquipo}
        >
          {(control) => (
            <select
              {...control}
              className="min-h-11 w-full rounded-[var(--radius-md)] border border-input bg-transparent px-3 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 aria-invalid:border-destructive"
              {...methods.register("equipo_id")}
            >
              <option value="">Elige el equipo</option>
              {equipos.map((equipo) => (
                <option key={equipo.id} value={equipo.id}>
                  {equipo.nombre}
                </option>
              ))}
            </select>
          )}
        </FormField>

        <FormField id={idRol} label="Rol" required span={6} error={errorRol}>
          {(control) => (
            <select
              {...control}
              className="min-h-11 w-full rounded-[var(--radius-md)] border border-input bg-transparent px-3 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 aria-invalid:border-destructive"
              {...methods.register("rol")}
            >
              {ROLES_PARTICIPANTE.map((rol) => (
                <option key={rol} value={rol}>
                  {rol}
                </option>
              ))}
            </select>
          )}
        </FormField>

        <FormFooter
          submitLabel="Asignar al equipo"
          pendingLabel="Asignando…"
          isSubmitting={agregar.isPending}
          isDisabled={equipos.length === 0}
        />
      </FormGrid>

      {mensaje ? (
        <Alert className="border-destructive/45 bg-destructive/10">
          <TriangleAlert
            className="size-4 text-destructive"
            aria-hidden="true"
          />
          <AlertTitle className="text-foreground">
            No pudimos asignar a la persona
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            {mensaje}
          </AlertDescription>
        </Alert>
      ) : null}

      {equipos.length === 0 ? (
        <p className="text-caption text-muted-foreground">
          La inscripción todavía no declara equipos: no hay a quién asignar a
          nadie.
        </p>
      ) : null}
    </form>
  );
}
