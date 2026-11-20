"use client";

import { Loader2, TriangleAlert } from "lucide-react";
import Link from "next/link";
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
import { handleApiError } from "@/errors";
import {
  type CompradorPaseData,
  CompradorPaseSchema,
  TIPOS_DOCUMENTO,
} from "../schemas/comprador-pase.schema";
import type {
  CompraPaseCreada,
  EnviarCompraPase,
  PaseCatalogo,
} from "../types/pase.types";
import { enlaceGestionCompra } from "../utils/pase.enlace.utils";

/** The fields the form owns. */
type Campos = "tipoDocumento" | "numeroDocumento" | "nombres" | "apellidos" | "contactoEmail";

export interface FormularioCompradorProps {
  /**
   * The transport of the request.
   *
   * While the prop is absent the form validates what was typed and then
   * says why the request cannot leave, instead of faking a purchase.
   */
  enviar?: EnviarCompraPase;
  /** The pass that is being bought. */
  pase: PaseCatalogo;
  /** The amount of passes that are being bought. */
  cantidad: number;
}

/** The phases of the form. */
type Fase = "inicial" | "enviando" | "sin-servicio" | "enviado" | "error-temporal";

/**
 * The summary of the errors of the form.
 *
 * It receives the focus after an invalid submit (`SH-02` A11Y-05) and it is
 * announced: it is an alert, not a paragraph.
 */
function ResumenErrores({
  methods,
}: {
  methods: UseFormReturn<CompradorPaseData>;
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
  methods: UseFormReturn<CompradorPaseData>;
}) {
  const id = "comprador-tipo-documento";
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
  methods: UseFormReturn<CompradorPaseData>;
  name: Campos;
  etiqueta: string;
  type?: string;
  autoComplete?: string;
  placeholder?: string;
}) {
  const id = `comprador-${name}`;
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
 * FormularioComprador - the identity of the buyer of a batch of passes.
 *
 * The buyer is a CIVIL identity: they may not have an account and the server
 * never creates one for them (`FL-06` paso 2). The form is the Mode 1
 * (`children`) of `GenericForm`: the label and the error of every field are
 * drawn ONCE, here, and the truth lives in Zod (`contract/smart.md` §5.2).
 *
 * The form does NOT ask for the attendees: the pass is nominative and the
 * assignment happens AFTER the payment, in the management link.
 */
export function FormularioComprador({
  enviar,
  pase,
  cantidad,
}: FormularioCompradorProps) {
  const [fase, setFase] = useState<Fase>("inicial");
  const [compra, setCompra] = useState<CompraPaseCreada | null>(null);
  const [mensajeError, setMensajeError] = useState<string | null>(null);

  const valoresIniciales: CompradorPaseData = {
    tipoDocumento: "DNI",
    numeroDocumento: "",
    nombres: "",
    apellidos: "",
    contactoEmail: "",
  };

  async function alEnviar(datos: CompradorPaseData) {
    if (!enviar) {
      setFase("sin-servicio");
      return;
    }

    setFase("enviando");
    setMensajeError(null);

    try {
      const creada = await enviar(pase, cantidad, datos);
      setCompra(creada ?? null);
      setFase("enviado");
    } catch (error) {
      setFase("error-temporal");
      setMensajeError(handleApiError(error).message);
    }
  }

  return (
    <GenericForm<CompradorPaseData>
      schema={CompradorPaseSchema}
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
            name="contactoEmail"
            etiqueta="Correo de contacto (opcional)"
            type="email"
            autoComplete="email"
          />

          <div className="flex flex-col gap-3">
            <Button
              type="submit"
              disabled={isSubmitting || fase === "enviando"}
              className="min-h-11 w-full"
            >
              {isSubmitting || fase === "enviando" ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  Enviando…
                </>
              ) : (
                "Continuar al pago"
              )}
            </Button>

            <p className="text-caption text-muted-foreground">
              El comprador puede ser una persona distinta de quienes asisten
              a la fiesta.
            </p>

            {fase === "sin-servicio" ? (
              <Alert>
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>La compra todavía no está disponible</AlertTitle>
                <AlertDescription>
                  No se ha creado ninguna compra. Vuelve a intentarlo en unos
                  segundos.
                </AlertDescription>
              </Alert>
            ) : null}

            {fase === "enviado" ? (
              <Alert>
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>Compra registrada</AlertTitle>
                <AlertDescription>
                  Tu compra está pendiente de pago. Guarda el enlace de gestión
                  para asignar las entradas cuando el pago se confirme.
                </AlertDescription>
                {compra ? (
                  <Link
                    href={enlaceGestionCompra(compra)}
                    className="text-sm font-semibold text-primary underline-offset-4 hover:underline"
                  >
                    Abrir la gestión de mi compra
                  </Link>
                ) : null}
              </Alert>
            ) : null}

            {fase === "error-temporal" ? (
              <Alert variant="destructive">
                <TriangleAlert className="size-4" aria-hidden="true" />
                <AlertTitle>No pudimos registrar la compra</AlertTitle>
                <AlertDescription>
                  {mensajeError ??
                    "Vuelve a intentarlo en unos segundos. Si el pago se cobró, la compra sigue existiendo y puedes retomarla con el enlace de gestión."}
                </AlertDescription>
              </Alert>
            ) : null}
          </div>
        </>
      )}
    </GenericForm>
  );
}
