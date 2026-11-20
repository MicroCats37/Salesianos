"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  CheckCircle2,
  Hash,
  IdCard,
  MessageSquareText,
  TriangleAlert,
  User,
  Users,
} from "lucide-react";
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
import {
  type AsignacionPaseData,
  AsignacionPaseSchema,
  TIPOS_DOCUMENTO,
} from "../schemas/comprador-pase.schema";
import { ResumenErrores } from "./ResumenErrores";

/** The values the form starts with. */
const VALORES_INICIALES: AsignacionPaseData = {
  tipoDocumento: "DNI",
  numeroDocumento: "",
  nombres: "",
  apellidos: "",
  motivo: "",
};

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
 * FormularioBeneficiario - the assignment of a pass to a person.
 *
 * The person is resolved by her CIVIL IDENTITY, never by an account: the
 * pass is nominative and the assignment happens after the payment, in the
 * management link (`FL-06`).
 *
 * The form is the Mode 1 (`children`) of `GenericForm`: the label, the icon
 * and the error of every field are drawn ONCE, by `FormField`, and the truth
 * lives in Zod (`contract/smart.md` §5.2).
 *
 * The DNI is NEVER a credential: the link's token is what opens the batch
 * (`RN-U04`), and the form never asks for it.
 */
export function FormularioBeneficiario({
  enviar,
  hayCupo = true,
}: FormularioBeneficiarioProps) {
  const [fase, setFase] = useState<Fase>("inicial");

  /**
   * The methods live HERE and not inside the `GenericForm`.
   *
   * The document type is a CONTROLLED field (it is a `Select`, not an
   * `Input`), so it needs `useController`: a hook cannot be called inside the
   * render prop of `FormField`, and the form owns the methods so the
   * controller is declared at the top level of the component.
   */
  const methods = useForm<AsignacionPaseData>({
    resolver: zodResolver(AsignacionPaseSchema),
    defaultValues: VALORES_INICIALES,
  });

  const { field: tipoDocumento } = useController({
    control: methods.control,
    name: "tipoDocumento",
  });

  const errores = methods.formState.errors;

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
      initialData={VALORES_INICIALES}
      formMethods={methods}
      onSubmit={alEnviar}
      formClassName="flex flex-col gap-4"
    >
      {({ isSubmitting }) => (
        <>
          <ResumenErrores methods={methods} />

          <FormGrid>
            <FormField
              id="beneficiario-tipo-documento"
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
              id="beneficiario-numero-documento"
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
              id="beneficiario-nombres"
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
              id="beneficiario-apellidos"
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
              id="beneficiario-motivo"
              label="Motivo (opcional)"
              icon={MessageSquareText}
              span={12}
              helper="La persona que usa el pase puede ser distinta de quien compró."
              error={errores.motivo?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  type="text"
                  placeholder="Por ejemplo: asiste con la familia"
                  {...methods.register("motivo")}
                />
              )}
            </FormField>

            <FormFooter
              submitLabel="Asignar el pase"
              pendingLabel="Asignando…"
              isSubmitting={isSubmitting || fase === "enviando"}
              isDisabled={!hayCupo}
            />
          </FormGrid>

          {!hayCupo ? (
            <p className="text-caption font-semibold text-destructive">
              No quedan pases por asignar en esta compra.
            </p>
          ) : null}

          {fase === "sin-servicio" ? (
            <Alert>
              <TriangleAlert className="size-4" aria-hidden="true" />
              <AlertTitle>La asignación todavía no está disponible</AlertTitle>
              <AlertDescription>
                No se ha enviado ninguna asignación. Vuelve a intentarlo en unos
                segundos.
              </AlertDescription>
            </Alert>
          ) : null}

          {fase === "enviado" ? (
            <Alert>
              <CheckCircle2 className="size-4" aria-hidden="true" />
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
                Vuelve a intentarlo en unos segundos. Si alguien más tiene ya
                una entrada de este pase, el servidor lo dirá.
              </AlertDescription>
            </Alert>
          ) : null}
        </>
      )}
    </GenericForm>
  );
}
