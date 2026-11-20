"use client";

import { Loader2, TriangleAlert } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useController, useWatch } from "react-hook-form";
import type { UseFormReturn } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  type AsignacionPaseData,
  AsignacionPaseSchema,
  TIPOS_DOCUMENTO,
} from "../schemas/comprador-pase.schema";

/** The fields the form owns. */
type Campos =
  | "tipoDocumento"
  | "numeroDocumento"
  | "nombres"
  | "apellidos"
  | "motivo";

export interface FormularioBeneficiarioProps {
  /**
   * The transport of the request.
   *
   * It is the mutation of the feature: the payload is built THERE, in the
   * hook, and never in this component.
   */
  enviar?: (datos: AsignacionPaseData) => Promise<void>;
  /** Whether the batch still has passes to share. */
  hayCupo?: boolean;
}

/** The phases of the form. */
type Fase =
  | "inicial"
  | "enviando"
  | "sin-servicio"
  | "enviado"
  | "error-temporal";

/**
 * The summary of the errors of the form.
 *
 * It receives the focus after an invalid submit (`SH-02` A11Y-05) and it is
 * announced: it is an alert, not a paragraph.
 */
function ResumenErrores({
  methods,
}: {
  methods: UseFormReturn<AsignacionPaseData>;
}) {
  const referencia = useRef<HTMLDivElement>(null);
  const { errors, isSubmitted } = methods.formState;

  const mensajes = Object.values(errors)
    .map((error) => error?.message)
    .filter((mensaje): mensaje is string => Boolean(mensaje));

  useEffect(() => {
    if (!isSubmitted || mensajes.length === 0) return;
    referencia.current?.focus();
  }, [isSubmitted, mensajes.length]);

  if (!isSubmitted || mensajes.length === 0) return null;

  return (
    <div
      ref={referencia}
      role="alert"
      tabIndex={-1}
      className="rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 px-3 py-2.5"
    >
      <p className="text-sm font-semibold text-foreground">
        Revisa{" "}
        {mensajes.length === 1 ? "este campo" : "estos campos"} antes de
        continuar.
      </p>
      <ul className="mt-1 flex flex-col gap-0.5">
        {mensajes.map((mensaje) => (
          <li key={mensaje} className="text-caption text-muted-foreground">
            {mensaje}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** The type of the civil document. */
function CampoTipoDocumento({
  methods,
}: {
  methods: UseFormReturn<AsignacionPaseData>;
}) {
  const id = "beneficiario-tipo-documento";
  const valor = useWatch({ control: methods.control, name: "tipoDocumento" });
  const { field, fieldState } = useController({
    control: methods.control,
    name: "tipoDocumento",
  });
  const error = fieldState.error?.message;

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>Tipo de documento</Label>
      <Select value={valor} onValueChange={field.onChange}>
        <SelectTrigger
          id={id}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          className="min-h-11 w-full"
        >
          <SelectValue placeholder="Elige el tipo de documento" />
        </SelectTrigger>
        <SelectContent>
          {TIPOS_DOCUMENTO.map((tipo) => (
            <SelectItem key={tipo} value={tipo}>
              {tipo}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error ? (
        <p id={`${id}-error`} className="text-caption text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** A text field of the form, with its label and its associated error. */
function CampoTexto({
  methods,
  name,
  etiqueta,
  type = "text",
  autoComplete,
  placeholder,
}: {
  methods: UseFormReturn<AsignacionPaseData>;
  name: Campos;
  etiqueta: string;
  type?: string;
  autoComplete?: string;
  placeholder?: string;
}) {
  const id = `beneficiario-${name}`;
  const error = methods.formState.errors[name]?.message;

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{etiqueta}</Label>
      <Input
        id={id}
        type={type}
        autoComplete={autoComplete}
        placeholder={placeholder}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        className="min-h-11"
        {...methods.register(name)}
      />
      {error ? (
        <p id={`${id}-error`} className="text-caption text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/**
 * FormularioBeneficiario - the assignment of a pass to a person.
 *
 * The person is resolved by her CIVIL IDENTITY, never by an account: the
 * pass is nominative and the assignment happens after the payment, in the
 * management link (`FL-06`).
 *
 * The form is the Mode 1 (`children`) of `GenericForm`: the label and the
 * error of every field are drawn ONCE, here, and the truth lives in Zod
 * (`contract/smart.md` §5.2).
 *
 * The DNI is NEVER a credential: the link's token is what opens the batch
 * (`RN-U04`), and the form never asks for it.
 */
export function FormularioBeneficiario({
  enviar,
  hayCupo = true,
}: FormularioBeneficiarioProps) {
  const [fase, setFase] = useState<Fase>("inicial");

  const valoresIniciales: AsignacionPaseData = {
    tipoDocumento: "DNI",
    numeroDocumento: "",
    nombres: "",
    apellidos: "",
    motivo: "",
  };

  async function alEnviar(datos: AsignacionPaseData) {
    if (!enviar) {
      setFase("sin-servicio");
      return;
    }

    setFase("enviando");

    try {
      await enviar(datos);
      setFase("enviado");
    } catch {
      setFase("error-temporal");
    }
  }

  return (
    <GenericForm<AsignacionPaseData>
      schema={AsignacionPaseSchema}
      initialData={valoresIniciales}
      onSubmit={alEnviar}
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting }) => (
        <>
          <ResumenErrores methods={methods} />

          <CampoTipoDocumento methods={methods} />
          <CampoTexto
            methods={methods}
            name="numeroDocumento"
            etiqueta="Número de documento"
            autoComplete="off"
          />
          <CampoTexto
            methods={methods}
            name="nombres"
            etiqueta="Nombres"
            autoComplete="name"
          />
          <CampoTexto
            methods={methods}
            name="apellidos"
            etiqueta="Apellidos"
            autoComplete="family-name"
          />
          <CampoTexto
            methods={methods}
            name="motivo"
            etiqueta="Motivo (opcional)"
            placeholder="Por ejemplo: asiste con la familia"
          />

          <div className="flex flex-col gap-3">
            <Button
              type="submit"
              disabled={isSubmitting || fase === "enviando" || !hayCupo}
              className="min-h-11 w-full"
            >
              {isSubmitting || fase === "enviando" ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  Asignando…
                </>
              ) : (
                "Asignar el pase"
              )}
            </Button>

            {!hayCupo ? (
              <p className="text-caption font-semibold text-destructive">
                No quedan pases por asignar en esta compra.
              </p>
            ) : null}

            <p className="text-caption text-muted-foreground">
              La persona que usa el pase puede ser distinta de quien compró.
            </p>

            {fase === "sin-servicio" ? (
              <Alert>
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>La asignación todavía no está disponible</AlertTitle>
                <AlertDescription>
                  No se ha enviado ninguna asignación. Vuelve a intentarlo en
                  unos segundos.
                </AlertDescription>
              </Alert>
            ) : null}

            {fase === "enviado" ? (
              <Alert>
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>Pase asignado</AlertTitle>
                <AlertDescription>
                  La persona ya tiene su entrada. Puedes revisar la lista de
                  titulares más abajo.
                </AlertDescription>
              </Alert>
            ) : null}

            {fase === "error-temporal" ? (
              <Alert variant="destructive">
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>No pudimos asignar el pase</AlertTitle>
                <AlertDescription>
                  Vuelve a intentarlo en unos segundos. Si alguien más tiene
                  ya una entrada de este pase, el servidor lo dirá.
                </AlertDescription>
              </Alert>
            ) : null}
          </div>
        </>
      )}
    </GenericForm>
  );
}
