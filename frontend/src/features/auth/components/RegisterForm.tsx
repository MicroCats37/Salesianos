"use client";

import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Lock,
  Mail,
  Search,
  User,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Controller, useFormContext, useWatch } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRegister } from "@/features/auth/hooks";
import { useDocumentoLookup } from "@/features/inscripciones/hooks/useDocumentoLookup";
import { toast } from "sonner";
import {
  type RegisterFormData,
  RegisterFormSchema,
} from "@/features/auth/schemas";
import { cn, stripNonDigits } from "@/lib/utils";

// ── FieldWrapper ───────────────────────────────────────────────────────────────

interface FieldWrapperProps {
  label: string;
  error?: string;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
}

function FieldWrapper({
  label,
  error,
  required,
  className,
  children,
}: FieldWrapperProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <Label className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
          {label}
          {required && <span className="text-amber-500">*</span>}
        </Label>
      )}
      {children}
      {error && (
        <p className="flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="size-3.5 shrink-0" />
          {error}
        </p>
      )}
    </div>
  );
}

// ── Smart Components ────────────────────────────────────────────────────────────

interface SmartTextFieldProps {
  name: "nombres" | "apellidos" | "contactoEmergenciaNombre";
  label: string;
  placeholder?: string;
  icon?: React.ElementType;
  required?: boolean;
}

function SmartTextField({
  name,
  label,
  placeholder,
  icon: Icon,
  required,
}: SmartTextFieldProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors[name]?.message as string | undefined;

  return (
    <FieldWrapper label={label} error={error} required={required}>
      <div className="relative">
        {Icon && (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
            <Icon className="size-4" />
          </span>
        )}
        <Input
          {...register(name)}
          type="text"
          placeholder={placeholder}
          autoComplete={
            name === "nombres" || name === "apellidos" ? "name" : "off"
          }
          className={cn(
            Icon && "pl-9",
            "input-brand",
            error && "border-destructive ring-1 ring-destructive",
          )}
        />
      </div>
    </FieldWrapper>
  );
}

function SmartEmailField() {
  const {
    register,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors.email?.message as string | undefined;

  return (
    <FieldWrapper label="Email" error={error} required>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
          <Mail className="size-4" />
        </span>
        <Input
          {...register("email")}
          type="email"
          placeholder="tu@email.com"
          autoComplete="email"
          className={cn(
            "pl-9 input-brand",
            error && "border-destructive ring-1 ring-destructive",
          )}
        />
      </div>
    </FieldWrapper>
  );
}

function SmartPasswordField() {
  const {
    register,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors.password?.message as string | undefined;
  const [showPassword, setShowPassword] = useState(false);

  return (
    <FieldWrapper label="Contraseña" error={error} required>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
          <Lock className="size-4" />
        </span>
        <Input
          {...register("password")}
          type={showPassword ? "text" : "password"}
          placeholder="Mín. 8 caracteres"
          autoComplete="new-password"
          className={cn(
            "pl-9 pr-10 input-brand",
            error && "border-destructive ring-1 ring-destructive",
          )}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 transition-colors p-1"
          aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Eye className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </div>
    </FieldWrapper>
  );
}

function SmartConfirmPasswordField() {
  const {
    register,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors.confirmPassword?.message as string | undefined;
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <FieldWrapper label="Confirmar" error={error} required>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
          <CheckCircle2 className="size-4" />
        </span>
        <Input
          {...register("confirmPassword")}
          type={showConfirmPassword ? "text" : "password"}
          placeholder="Repite la contraseña"
          autoComplete="new-password"
          className={cn(
            "pl-9 pr-10 input-brand",
            error && "border-destructive ring-1 ring-destructive",
          )}
        />
        <button
          type="button"
          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 transition-colors p-1"
          aria-label={showConfirmPassword ? "Ocultar confirmación" : "Mostrar confirmación"}
        >
          {showConfirmPassword ? (
            <EyeOff className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Eye className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </div>
    </FieldWrapper>
  );
}

const TIPO_DOCUMENTO_OPTIONS = [
  { label: "DNI", value: "DNI" as const },
  { label: "CE", value: "CE" as const },
  { label: "PAS", value: "PAS" as const },
];

function SmartTipoDocumentoField() {
  const {
    control,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors.tipoDocumento?.message as string | undefined;

  return (
    <FieldWrapper label="Tipo de documento" error={error} required>
      <Controller
        name="tipoDocumento"
        control={control}
        render={({ field }) => (
          <Select onValueChange={field.onChange} value={field.value}>
            <SelectTrigger
              className={cn(
                "input-brand w-full",
                error && "border-destructive ring-1 ring-destructive",
              )}
            >
              
              <SelectValue placeholder="Selecciona" className="pl-7" />
            </SelectTrigger>
            <SelectContent>
              {TIPO_DOCUMENTO_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />
    </FieldWrapper>
  );
}

function SmartNumeroDocumentoField() {
  const {
    control,
    formState: { errors },
    setValue,
    trigger,
  } = useFormContext<RegisterFormData>();
  const documentoLookup = useDocumentoLookup();

  const tipoDocumento = useWatch({ control, name: "tipoDocumento" }) ?? "DNI";
  const numeroDocumento =
    useWatch({ control, name: "numeroDocumento" }) ?? "";
  const error = errors.numeroDocumento?.message as string | undefined;

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
        toast.error("La respuesta del documento no contiene nombres completos");
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
      toast.success("Datos del documento cargados");
    } catch {
      /* hook ya tostó el error */
    }
  }

  return (
    <FieldWrapper label="Número de documento" error={error} required>
      <div className="flex items-stretch gap-2">
        <div className="flex-1">
          <Controller
            name="numeroDocumento"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                type="text"
                inputMode={inputMode}
                autoComplete="off"
                placeholder={placeholder}
                maxLength={maxLen}
                className={cn(
                  "input-brand",
                  error && "border-destructive ring-1 ring-destructive",
                )}
                onChange={(e) => {
                  const filtered =
                    tipoDocumento === "PAS"
                      ? e.target.value
                          .replace(/[^a-zA-Z0-9]/g, "")
                          .toUpperCase()
                          .slice(0, maxLen)
                      : stripNonDigits(e.target.value).slice(0, maxLen);
                  field.onChange({ target: { value: filtered } });
                }}
              />
            )}
          />
        </div>
        {tipoDocumento === "DNI" && (
          <Button
            type="button"
            variant="default"
            size="icon"
            disabled={!canLookup || documentoLookup.isPending}
            onClick={handleLookup}
            aria-label="Buscar nombres por DNI"
            className="h-11 w-11 rounded-xl bg-[var(--gold)] text-brand-deep-navy hover:bg-[var(--gold)]/90 shadow"
          >
            {documentoLookup.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Search className="size-4" />
            )}
          </Button>
        )}
      </div>
    </FieldWrapper>
  );
}

interface SmartSelectFieldProps {
  name: "genero";
  label: string;
  icon?: React.ElementType;
  placeholder?: string;
  options: { label: string; value: string }[];
  required?: boolean;
}

function SmartSelectField({
  name,
  label,
  icon: Icon,
  placeholder,
  options,
  required,
}: SmartSelectFieldProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors[name]?.message as string | undefined;

  return (
    <FieldWrapper label={label} error={error} required={required}>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <Select onValueChange={field.onChange} value={field.value}>
            <SelectTrigger
              className={cn(
                "input-brand w-full",
                error && "border-destructive ring-1 ring-destructive",
              )}
            >
              
              <SelectValue
                placeholder={placeholder ?? "Selecciona"}
                className={cn(Icon && "pl-9")}
              />
            </SelectTrigger>
            <SelectContent>
              {options.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />
    </FieldWrapper>
  );
}

function SmartAcceptedBasesCheckboxField() {
  const {
    control,
    formState: { errors },
  } = useFormContext<RegisterFormData>();
  const error = errors.acceptedBases?.message as string | undefined;

  return (
    <div className="flex items-start gap-3 rounded-xl border-2 border-[var(--gold)]/40 surface-form-amber p-4">
      <Controller
        name="acceptedBases"
        control={control}
        render={({ field }) => (
          <Checkbox
            id="acceptedBases"
            checked={field.value === true}
            onCheckedChange={(checked) =>
              field.onChange((checked as boolean) === true)
            }
            className="mt-0.5"
          />
        )}
      />
      <div className="flex-1">
        <Label
          htmlFor="acceptedBases"
          className="cursor-pointer font-bold leading-tight text-brand-deep-navy"
        >
          He leído y acepto las bases oficiales del evento.
        </Label>
      </div>
      {error && (
        <p className="flex items-center gap-1.5 text-sm text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          {error}
        </p>
      )}
    </div>
  );
}

// ── RegisterForm ──────────────────────────────────────────────────────────────

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
        formClassName="space-y-3"
        showErrorsAsToasts
      >
        {({ isSubmitting }) => (
          <>
            {/* Compact branding header */}
            <div className="flex flex-col items-center gap-2 pb-4">
              <FestBrandHeader
                variant="onLight"
                size="sm"
                subtitle="Crear cuenta · Unete y preinscribe a tu promocion"
              />
            </div>

            {/* F1 — Email: full width */}
            <SmartEmailField />

            {/* F2 — Password | Confirmar: 50/50 */}
            <div className="grid gap-3 md:grid-cols-2">
              <SmartPasswordField />
              <SmartConfirmPasswordField />
            </div>

            {/* F3 — Tipo doc | Número doc: 50/50 */}
            <div className="grid gap-3 md:grid-cols-2">
              <SmartTipoDocumentoField />
              <SmartNumeroDocumentoField />
            </div>

            {/* F4 — Nombres | Apellidos: 50/50 */}
            <div className="grid gap-3 md:grid-cols-2">
              <SmartTextField
                name="nombres"
                label="Nombres"
                placeholder="Juan Carlos"
                icon={User}
                required
              />
              <SmartTextField
                name="apellidos"
                label="Apellidos"
                placeholder="Pérez López"
                icon={User}
                required
              />
            </div>

            {/* F5 — Género: full width */}
            <SmartSelectField
              name="genero"
              label="Género"
              icon={User}
              placeholder="Selecciona"
              options={[
                { label: "Masculino", value: "M" },
                { label: "Femenino", value: "F" },
              ]}
              required
            />

            {/* F6 — Acepto bases: full width, yellow panel */}
            <SmartAcceptedBasesCheckboxField />

            {/* F9 — Submit button + login link */}
            <div className="flex flex-col gap-3 pt-1">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="btn-brand-gradient btn-shine h-12 w-full rounded-xl text-base font-black uppercase tracking-wider"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    Creando cuenta...
                  </>
                ) : (
                  "Crear cuenta"
                )}
              </Button>
              <p className="text-center text-sm text-slate-600">
                ¿Ya tienes cuenta?{" "}
                <Link
                  href="/login"
                  className="font-bold text-indigo-700 underline-offset-4 hover:underline"
                >
                  Inicia sesión
                </Link>
              </p>
            </div>
          </>
        )}
      </GenericForm>
    </div>
  );
}
