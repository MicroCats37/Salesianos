"use client";

import { Mail, MailCheck, Receipt, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { FormField } from "@/components/forms/FormField";
import { FormFooter } from "@/components/forms/FormFooter";
import { FormGrid } from "@/components/forms/FormGrid";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { ResumenErrores } from "@/features/pases/components/ResumenErrores";
import {
  type RecuperarCompraFormData,
  RecuperarCompraFormSchema,
} from "../schemas/recuperar-compra.schema";

/**
 * The outcome of a recovery request.
 *
 * The answer is NEUTRAL: it is the same whether the purchase exists or not,
 * so it never says that a purchase was found (RB-02 REC-01).
 */
export type ResultadoRecuperacion =
  | { tipo: "neutro" }
  | { tipo: "limitado"; reintentarEn: string }
  | { tipo: "error-temporal" };

export interface RecuperarCompraFormProps {
  /**
   * The transport of the request.
   *
   * It does NOT exist yet, and API-01 could not add it: the endpoint
   * `RT-RC-01` (`POST /recuperar-compra`) has NO registered route in
   * `Aplicacion/backend/config/api.py` and NO frozen presenter, and the mail
   * provider is not configured either (`PD-08`). While the prop is absent the
   * form says so instead of faking an answer. When the backend owns the route,
   * the transport is handed to this prop and nothing else changes.
   */
  enviar?: (datos: RecuperarCompraFormData) => Promise<ResultadoRecuperacion>;
}

type Fase =
  | "inicial"
  | "enviando"
  | "sin-servicio"
  | "neutro"
  | "limitado"
  | "error-temporal";

/**
 * The outcome of the request.
 *
 * Every outcome is NEUTRAL about the existence of the purchase: none of them
 * says that a purchase was found. The state is announced, because the answer
 * arrives after the person already sent the form.
 */
function ResultadoDelFormulario({ fase }: { fase: Fase }) {
  if (fase === "inicial" || fase === "enviando") return null;

  if (fase === "sin-servicio") {
    return (
      <Alert className="border-warning/45 bg-warning/12">
        <TriangleAlert className="size-4 text-warning" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          El envío de correos está desactivado por ahora
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          El servicio de correo todavía no está habilitado en esta edición, así
          que la solicitud no se ha enviado. Tu compra sigue intacta: cuando el
          servicio esté activo podrás pedir el enlace otra vez.
        </AlertDescription>
      </Alert>
    );
  }

  if (fase === "neutro") {
    return (
      <Alert className="border-info/45 bg-info/12">
        <MailCheck className="size-4 text-info" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          Solicitud registrada
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          Si encontramos una compra con esos datos, te enviamos un enlace nuevo.
          La respuesta es la misma exista o no la compra, y pedirla dos veces no
          vuelve a abrir ninguna compra.
        </AlertDescription>
      </Alert>
    );
  }

  if (fase === "limitado") {
    return (
      <Alert className="border-warning/45 bg-warning/12">
        <TriangleAlert className="size-4 text-warning" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          Has pedido demasiados enlaces
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          Para proteger tu compra limitamos cuántas veces se puede pedir un
          enlace. Vuelve a intentarlo más tarde.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Alert className="border-destructive/45 bg-destructive/10">
      <TriangleAlert className="size-4 text-destructive" aria-hidden="true" />
      <AlertTitle className="text-foreground">
        No pudimos registrar la solicitud
      </AlertTitle>
      <AlertDescription className="text-muted-foreground">
        Vuelve a intentarlo en unos segundos. Tu compra no se ha modificado.
      </AlertDescription>
    </Alert>
  );
}

/**
 * RecuperarCompraForm - the form of the recovery of a purchase.
 *
 * The form asks for the minimum that identifies a purchase and it never
 * reveals whether that purchase exists: the answer is the same either way.
 *
 * While the mail provider is not configured (PD-08) the form does NOT fake a
 * sent message: it validates what was typed and then says why the request
 * cannot leave yet.
 *
 * It is the Mode 1 (`children`) of `GenericForm`: the label, the icon and the
 * error of every field are drawn ONCE, by `FormField`, and the truth lives
 * in Zod (`contract/smart.md` §5.2). The summary of the errors is the one of
 * the feature: it announces the errors and it takes the focus after an
 * invalid submit (`SH-02` A11Y-05).
 */
export function RecuperarCompraForm({ enviar }: RecuperarCompraFormProps) {
  const [fase, setFase] = useState<Fase>("inicial");

  const valoresIniciales: RecuperarCompraFormData = {
    correo: "",
    numeroOrden: "",
  };

  async function alEnviar(datos: RecuperarCompraFormData) {
    if (!enviar) {
      setFase("sin-servicio");
      return;
    }

    setFase("enviando");

    try {
      const resultado = await enviar(datos);
      setFase(resultado.tipo === "neutro" ? "neutro" : resultado.tipo);
    } catch {
      setFase("error-temporal");
    }
  }

  return (
    <GenericForm<RecuperarCompraFormData>
      schema={RecuperarCompraFormSchema}
      initialData={valoresIniciales}
      onSubmit={alEnviar}
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting }) => {
        const { register, formState } = methods;

        return (
          <>
            <ResumenErrores methods={methods} />

            <FormGrid>
              <FormField
                id="correo"
                label="Correo de la compra"
                required
                icon={Mail}
                span={12}
                error={formState.errors.correo?.message}
              >
                {(control) => (
                  <Input
                    {...control}
                    {...register("correo")}
                    type="email"
                    inputMode="email"
                    autoComplete="email"
                    placeholder="tu@email.com"
                  />
                )}
              </FormField>

              <FormField
                id="numeroOrden"
                label="Número de orden"
                required
                icon={Receipt}
                span={12}
                error={formState.errors.numeroOrden?.message}
              >
                {(control) => (
                  <Input
                    {...control}
                    {...register("numeroOrden")}
                    type="text"
                    autoComplete="off"
                    placeholder="El número que aparece en tu comprobante"
                  />
                )}
              </FormField>

              <FormFooter
                submitLabel="Solicitar el enlace"
                pendingLabel="Enviando…"
                isSubmitting={isSubmitting || fase === "enviando"}
              />
            </FormGrid>

            <p className="text-caption text-muted-foreground">
              Por seguridad confirmamos siempre lo mismo, exista o no una compra
              con esos datos.
            </p>

            <ResultadoDelFormulario fase={fase} />
          </>
        );
      }}
    </GenericForm>
  );
}
