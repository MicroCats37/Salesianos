"use client";

import { AlertCircle, Loader2, Mail, MailCheck, Receipt, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";
import { useFormContext } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
 * The fields of the form.
 *
 * They are drawn inside the GenericForm wrapper, so the label and the error
 * of a field are rendered ONCE (contract/smart.md 5.2).
 */
function CampoCorreo() {
  const {
    register,
    formState: { errors },
  } = useFormContext<RecuperarCompraFormData>();
  const error = errors.correo?.message;

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor="correo" className="text-sm font-semibold text-foreground">
        Correo de la compra
      </Label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
          <Mail className="size-4" aria-hidden="true" />
        </span>
        <Input
          {...register("correo")}
          id="correo"
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="tu@email.com"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "correo-error" : undefined}
          className="min-h-11 pl-9"
        />
      </div>
      {error ? (
        <p
          id="correo-error"
          className="flex items-center gap-1.5 text-xs text-destructive"
        >
          <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
          {error}
        </p>
      ) : null}
    </div>
  );
}

function CampoNumeroOrden() {
  const {
    register,
    formState: { errors },
  } = useFormContext<RecuperarCompraFormData>();
  const error = errors.numeroOrden?.message;

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor="numeroOrden" className="text-sm font-semibold text-foreground">
        Número de orden
      </Label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
          <Receipt className="size-4" aria-hidden="true" />
        </span>
        <Input
          {...register("numeroOrden")}
          id="numeroOrden"
          type="text"
          autoComplete="off"
          placeholder="El número que aparece en tu comprobante"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "numeroOrden-error" : undefined}
          className="min-h-11 pl-9"
        />
      </div>
      {error ? (
        <p
          id="numeroOrden-error"
          className="flex items-center gap-1.5 text-xs text-destructive"
        >
          <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
          {error}
        </p>
      ) : null}
    </div>
  );
}

/**
 * The summary of the errors of the form.
 *
 * It receives the focus after an invalid submit (SH-02 A11Y-05) and it is
 * announced: it is an alert, not a paragraph.
 */
function ResumenErrores() {
  const {
    formState: { errors, isSubmitted },
  } = useFormContext<RecuperarCompraFormData>();
  const referencia = useRef<HTMLDivElement>(null);

  const mensajes = Object.values(errors)
    .map((error) => error?.message)
    .filter((mensaje): mensaje is string => Boolean(mensaje));

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
          que la solicitud no se ha enviado. Tu compra sigue intacta: cuando
          el servicio esté activo podrás pedir el enlace otra vez.
        </AlertDescription>
      </Alert>
    );
  }

  if (fase === "neutro") {
    return (
      <Alert className="border-info/45 bg-info/12">
        <MailCheck className="size-4 text-info" aria-hidden="true" />
        <AlertTitle className="text-foreground">Solicitud registrada</AlertTitle>
        <AlertDescription className="text-muted-foreground">
          Si encontramos una compra con esos datos, te enviamos un enlace
          nuevo. La respuesta es la misma exista o no la compra, y pedirla dos
          veces no vuelve a abrir ninguna compra.
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
      {({ isSubmitting }) => (
        <>
          <ResumenErrores />

          <CampoCorreo />
          <CampoNumeroOrden />

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
                "Solicitar el enlace"
              )}
            </Button>

            <p className="text-caption text-muted-foreground">
              Por seguridad confirmamos siempre lo mismo, exista o no una compra
              con esos datos.
            </p>

            <ResultadoDelFormulario fase={fase} />
          </div>
        </>
      )}
    </GenericForm>
  );
}

