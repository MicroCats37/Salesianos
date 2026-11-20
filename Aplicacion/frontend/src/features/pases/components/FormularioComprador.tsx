"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Hash, IdCard, Mail, TriangleAlert, User, Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useController, useForm } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormFooter } from "@/components/forms/FormFooter";
import { FormGrid } from "@/components/forms/FormGrid";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
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
import { ResumenErrores } from "./ResumenErrores";

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
type Fase =
  | "inicial"
  | "enviando"
  | "sin-servicio"
  | "enviado"
  | "error-temporal";

/**
 * FormularioComprador - the identity of the buyer of a batch of passes.
 *
 * The buyer is a CIVIL identity: they may not have an account and the server
 * never creates one for them (`FL-06` paso 2). The form is the Mode 1
 * (`children`) of `GenericForm`: the label, the icon and the error of every
 * field are drawn ONCE, by `FormField`, and the truth lives in Zod
 * (`contract/smart.md` §5.2).
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

  /**
   * The methods live HERE and not inside the `GenericForm`.
   *
   * The document type is a CONTROLLED field (it is a `Select`, not an
   * `Input`), so it needs `useController`: a hook cannot be called inside the
   * render prop of `FormField`, and the form owns the methods so the
   * controller is declared at the top level of the component.
   */
  const methods = useForm<CompradorPaseData>({
    resolver: zodResolver(CompradorPaseSchema),
    defaultValues: valoresIniciales,
  });

  const { field: tipoDocumento } = useController({
    control: methods.control,
    name: "tipoDocumento",
  });

  const errores = methods.formState.errors;

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
      formMethods={methods}
      onSubmit={alEnviar}
      formClassName="flex flex-col gap-4"
    >
      {({ isSubmitting }) => (
        <>
          <ResumenErrores methods={methods} />

          <FormGrid>
            <FormField
              id="comprador-tipo-documento"
              label="Tipo de documento"
              required
              icon={IdCard}
              span={6}
              error={errores.tipoDocumento?.message}
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
              )}
            </FormField>

            <FormField
              id="comprador-numero-documento"
              label="Número de documento"
              required
              icon={Hash}
              span={6}
              error={errores.numeroDocumento?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  type="text"
                  autoComplete="off"
                  {...methods.register("numeroDocumento")}
                />
              )}
            </FormField>

            <FormField
              id="comprador-nombres"
              label="Nombres"
              required
              icon={User}
              span={6}
              error={errores.nombres?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  type="text"
                  autoComplete="name"
                  {...methods.register("nombres")}
                />
              )}
            </FormField>

            <FormField
              id="comprador-apellidos"
              label="Apellidos"
              icon={Users}
              span={6}
              error={errores.apellidos?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  type="text"
                  autoComplete="family-name"
                  {...methods.register("apellidos")}
                />
              )}
            </FormField>

            <FormField
              id="comprador-contacto-email"
              label="Correo de contacto (opcional)"
              icon={Mail}
              span={12}
              helper="El comprador puede ser una persona distinta de quienes asisten a la fiesta."
              error={errores.contactoEmail?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  type="email"
                  autoComplete="email"
                  {...methods.register("contactoEmail")}
                />
              )}
            </FormField>

            <FormFooter
              submitLabel="Continuar al pago"
              pendingLabel="Enviando…"
              isSubmitting={isSubmitting || fase === "enviando"}
            />
          </FormGrid>

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
        </>
      )}
    </GenericForm>
  );
}
