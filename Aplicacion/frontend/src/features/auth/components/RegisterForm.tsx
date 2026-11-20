"use client";

import {
  Hash,
  IdCard,
  Loader2,
  Lock,
  Mail,
  Search,
  User,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { Controller, useWatch } from "react-hook-form";
import { FestBrandHeader } from "@/components/brand/FestBrandHeader";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notify } from "@/errors";
import { ToggleContrasena } from "@/features/auth/components/ToggleContrasena";
import { useRegister } from "@/features/auth/hooks";
import { useDocumentoLookup } from "@/features/auth/hooks/useDocumentoLookup";
import {
  type RegisterFormData,
  RegisterFormSchema,
} from "@/features/auth/schemas";
import { RUTAS } from "@/lib/routes";
import { stripNonDigits } from "@/lib/utils";

const TIPO_DOCUMENTO_OPTIONS = [
  { label: "DNI", value: "DNI" as const },
  { label: "CE", value: "CE" as const },
  { label: "PAS", value: "PAS" as const },
];

const GENERO_OPTIONS = [
  { label: "Masculino", value: "M" },
  { label: "Femenino", value: "F" },
];

/**
 * A password of the form.
 *
 * The label, the icon, the error and the accessible names of the toggle are
 * drawn ONCE, by `FormField` and by `ToggleContrasena`.
 */
function CampoContrasena({
  methods,
  id,
  name,
  label,
  placeholder,
  autoComplete,
  campo,
}: {
  methods: UseFormReturn<RegisterFormData>;
  id: string;
  name: "password" | "confirmPassword";
  label: string;
  placeholder: string;
  autoComplete: string;
  campo: "contraseña" | "confirmación de la contraseña";
}) {
  const [visible, setVisible] = useState(false);
  const error = methods.formState.errors[name]?.message as string | undefined;

  return (
    <FormField
      id={id}
      label={label}
      required
      icon={Lock}
      span={6}
      error={error}
    >
      {(control) => (
        <div className="relative">
          <Input
            {...control}
            {...methods.register(name)}
            type={visible ? "text" : "password"}
            placeholder={placeholder}
            autoComplete={autoComplete}
            className="pr-12"
          />
          <ToggleContrasena
            visible={visible}
            onToggle={() => setVisible((actual) => !actual)}
            campo={campo}
          />
        </div>
      )}
    </FormField>
  );
}

/**
 * The type of the civil document.
 *
 * It is a CONTROLLED field, so it needs a `Controller`: the value lives in
 * the form and the document number reads it.
 */
function CampoTipoDocumento({
  methods,
}: {
  methods: UseFormReturn<RegisterFormData>;
}) {
  const error = methods.formState.errors.tipoDocumento?.message as
    | string
    | undefined;

  return (
    <FormField
      id="registro-tipo-documento"
      label="Tipo de documento"
      required
      icon={IdCard}
      span={6}
      error={error}
    >
      {(control) => (
        <Controller
          name="tipoDocumento"
          control={methods.control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger
                {...control}
                onBlur={field.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Selecciona" />
              </SelectTrigger>
              <SelectContent>
                {TIPO_DOCUMENTO_OPTIONS.map((opcion) => (
                  <SelectItem key={opcion.value} value={opcion.value}>
                    {opcion.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      )}
    </FormField>
  );
}

/**
 * The number of the civil document.
 *
 * With a DNI of eight digits the form can ask the server for the names of
 * the person: the lookup is a HELP, never a requirement.
 */
function CampoNumeroDocumento({
  methods,
}: {
  methods: UseFormReturn<RegisterFormData>;
}) {
  const documentoLookup = useDocumentoLookup();
  const { setValue, trigger } = methods;

  const tipoDocumento =
    useWatch({ control: methods.control, name: "tipoDocumento" }) ?? "DNI";
  const numeroDocumento =
    useWatch({ control: methods.control, name: "numeroDocumento" }) ?? "";
  const error = methods.formState.errors.numeroDocumento?.message as
    | string
    | undefined;

  const maxLen = tipoDocumento === "DNI" ? 8 : tipoDocumento === "CE" ? 9 : 20;
  const placeholder =
    tipoDocumento === "DNI"
      ? "12345678"
      : tipoDocumento === "CE"
        ? "123456789"
        : "ABC123456";
  const inputMode = tipoDocumento === "PAS" ? "text" : "numeric";
  const canLookup = tipoDocumento === "DNI" && numeroDocumento.length === 8;

  // Reset numeroDocumento and clear auto-filled names when tipoDocumento changes
  const prevTipoRef = useRef(tipoDocumento);
  useEffect(() => {
    if (prevTipoRef.current !== tipoDocumento) {
      prevTipoRef.current = tipoDocumento;
      setValue("numeroDocumento", "", { shouldValidate: true });
      setValue("nombres", "", { shouldValidate: false });
      setValue("apellidos", "", { shouldValidate: false });
    }
  }, [tipoDocumento, setValue]);

  async function handleLookup() {
    const valid = await trigger("numeroDocumento");
    if (!valid) return;
    try {
      const result = await documentoLookup.mutateAsync(numeroDocumento);
      if (!result.nombres || !result.apellidos) {
        notify.error(
          "La respuesta del documento no contiene nombres completos",
        );
        return;
      }
      setValue("numeroDocumento", result.numero_documento, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      });
      setValue("apellidos", result.apellidos, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      });
      setValue("nombres", result.nombres, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      });
      await trigger(["numeroDocumento", "nombres", "apellidos"]);
      notify.success("Datos del documento cargados");
    } catch {
      /* hook ya tostó el error */
    }
  }

  return (
    <FormField
      id="registro-numero-documento"
      label="Número de documento"
      required
      icon={Hash}
      span={6}
      error={error}
    >
      {(control) => (
        <div className="flex items-stretch gap-2">
          <Controller
            name="numeroDocumento"
            control={methods.control}
            render={({ field }) => (
              <Input
                {...control}
                {...field}
                type="text"
                inputMode={inputMode}
                autoComplete="off"
                placeholder={placeholder}
                maxLength={maxLen}
                onChange={(evento) => {
                  const filtrado =
                    tipoDocumento === "PAS"
                      ? evento.target.value
                          .replace(/[^a-zA-Z0-9]/g, "")
                          .toUpperCase()
                          .slice(0, maxLen)
                      : stripNonDigits(evento.target.value).slice(0, maxLen);
                  field.onChange({ target: { value: filtrado } });
                }}
              />
            )}
          />
          {tipoDocumento === "DNI" ? (
            <Button
              type="button"
              variant="default"
              size="icon"
              disabled={!canLookup || documentoLookup.isPending}
              onClick={handleLookup}
              aria-label="Buscar nombres por DNI"
              className="min-h-11 min-w-11 rounded-xl bg-accent text-accent-foreground shadow transition-colors duration-(--motion-duration-fast) hover:bg-accent/90"
            >
              {documentoLookup.isPending ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <Search className="size-4" aria-hidden="true" />
              )}
            </Button>
          ) : null}
        </div>
      )}
    </FormField>
  );
}

/**
 * The gender of the person.
 *
 * It is a CONTROLLED field: the value is one of the options the server
 * declared.
 */
function CampoGenero({
  methods,
}: {
  methods: UseFormReturn<RegisterFormData>;
}) {
  const error = methods.formState.errors.genero?.message as string | undefined;

  return (
    <FormField
      id="registro-genero"
      label="Género"
      required
      icon={User}
      span={12}
      error={error}
    >
      {(control) => (
        <Controller
          name="genero"
          control={methods.control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger
                {...control}
                onBlur={field.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Selecciona" />
              </SelectTrigger>
              <SelectContent>
                {GENERO_OPTIONS.map((opcion) => (
                  <SelectItem key={opcion.value} value={opcion.value}>
                    {opcion.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      )}
    </FormField>
  );
}

/**
 * The acceptance of the official bases.
 *
 * It is a FIELD and it is drawn like the rest of them: the label is the
 * sentence that the person accepts and the error lives under its control.
 */
function CampoBasesAceptadas({
  methods,
}: {
  methods: UseFormReturn<RegisterFormData>;
}) {
  const error = methods.formState.errors.acceptedBases?.message as
    | string
    | undefined;

  return (
    <div className="col-span-12 rounded-xl border-2 border-accent/40 bg-accent/10 p-4">
      <FormField
        id="registro-bases"
        label="He leído y acepto las bases oficiales del evento."
        required
        error={error}
      >
        {(control) => (
          <Controller
            name="acceptedBases"
            control={methods.control}
            render={({ field }) => (
              <Checkbox
                {...control}
                checked={field.value === true}
                onCheckedChange={(marcado) =>
                  field.onChange((marcado as boolean) === true)
                }
              />
            )}
          />
        )}
      </FormField>
    </div>
  );
}

/**
 * RegisterForm - the creation of the account.
 *
 * The form is the Mode 1 (`children`) of `GenericForm`: the label, the icon
 * and the error of every field are drawn ONCE, by `FormField`, and the truth
 * lives in Zod (`contract/smart.md` §5.2).
 */
export function RegisterForm() {
  const registerMutation = useRegister();

  const initialData: RegisterFormData = {
    email: "",
    password: "",
    confirmPassword: "",
    tipoDocumento: "DNI",
    numeroDocumento: "",
    nombres: "",
    apellidos: "",
    genero: "M",
    telefono: null,
    whatsapp: null,
    contactoEmergenciaNombre: null,
    contactoEmergenciaTelefono: null,
    acceptedBases: false as unknown as true,
  };

  const onSubmit = async (data: RegisterFormData) => {
    await registerMutation.mutateAsync(data);
  };

  return (
    <div className="w-full">
      <GenericForm<RegisterFormData>
        schema={RegisterFormSchema}
        initialData={initialData}
        onSubmit={onSubmit}
        formClassName="flex flex-col gap-4"
        showErrorsAsToasts
      >
        {({ methods, isSubmitting }) => {
          const { register, formState } = methods;

          return (
            <>
              {/* Compact branding header */}
              <div className="flex flex-col items-center gap-2 pb-4">
                <FestBrandHeader
                  variant="onLight"
                  size="sm"
                  subtitle="Crear cuenta · Unete y preinscribe a tu promocion"
                />
              </div>

              <FormGrid>
                <FormField
                  id="registro-email"
                  label="Email"
                  required
                  icon={Mail}
                  span={12}
                  error={formState.errors.email?.message as string | undefined}
                >
                  {(control) => (
                    <Input
                      {...control}
                      {...register("email")}
                      type="email"
                      placeholder="tu@email.com"
                      autoComplete="email"
                    />
                  )}
                </FormField>

                <CampoContrasena
                  methods={methods}
                  id="registro-password"
                  name="password"
                  label="Contraseña"
                  placeholder="Mín. 8 caracteres"
                  autoComplete="new-password"
                  campo="contraseña"
                />

                <CampoContrasena
                  methods={methods}
                  id="registro-confirm-password"
                  name="confirmPassword"
                  label="Confirmar"
                  placeholder="Repite la contraseña"
                  autoComplete="new-password"
                  campo="confirmación de la contraseña"
                />

                <CampoTipoDocumento methods={methods} />

                <CampoNumeroDocumento methods={methods} />

                <FormField
                  id="registro-nombres"
                  label="Nombres"
                  required
                  icon={User}
                  span={6}
                  error={
                    formState.errors.nombres?.message as string | undefined
                  }
                >
                  {(control) => (
                    <Input
                      {...control}
                      {...register("nombres")}
                      type="text"
                      placeholder="Juan Carlos"
                      autoComplete="name"
                    />
                  )}
                </FormField>

                <FormField
                  id="registro-apellidos"
                  label="Apellidos"
                  required
                  icon={Users}
                  span={6}
                  error={
                    formState.errors.apellidos?.message as string | undefined
                  }
                >
                  {(control) => (
                    <Input
                      {...control}
                      {...register("apellidos")}
                      type="text"
                      placeholder="Pérez López"
                      autoComplete="family-name"
                    />
                  )}
                </FormField>

                <CampoGenero methods={methods} />

                <CampoBasesAceptadas methods={methods} />
              </FormGrid>

              {/* F9 — Submit button + login link */}
              <div className="flex flex-col gap-3 pt-1">
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-brand-gradient h-12 w-full rounded-xl text-base font-semibold"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2
                        className="size-4 animate-spin"
                        aria-hidden="true"
                      />
                      Creando cuenta…
                    </>
                  ) : (
                    "Crear cuenta"
                  )}
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  ¿Ya tienes cuenta?{" "}
                  <Link
                    href={RUTAS.auth.login}
                    className="font-semibold text-primary underline-offset-4 hover:underline"
                  >
                    Inicia sesión
                  </Link>
                </p>
              </div>
            </>
          );
        }}
      </GenericForm>
    </div>
  );
}
