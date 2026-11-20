"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { LucideIcon } from "lucide-react";
import { IdCard, KeyRound, Loader2, LogIn, Mail, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";
import { useForm } from "react-hook-form";
import { FestBrandHeader } from "@/components/brand/FestBrandHeader";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { handleApiError, notify } from "@/errors";
import { AuthGlassCard } from "@/features/auth/components/AuthGlassCard";
import { AuthShell } from "@/features/auth/components/AuthShell";
import { ToggleContrasena } from "@/features/auth/components/ToggleContrasena";
import { useLogin } from "@/features/auth/hooks";
import {
  type LoginDniFormData,
  LoginDniFormSchema,
  type LoginEmailFormData,
  LoginEmailFormSchema,
  type LoginUsernameFormData,
  LoginUsernameFormSchema,
} from "@/features/auth/schemas";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { resolverDeDestino } from "@/features/auth/utils/resolver-destino";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";

// =============================================================================
// TAB TYPES — ordered: DNI, Email, Usuario
// =============================================================================

type LoginTab = "dni" | "email" | "username";

const TAB_ORDER: LoginTab[] = ["dni", "email", "username"];

const TAB_LABELS: Record<LoginTab, string> = {
  dni: "DNI",
  email: "Email",
  username: "Usuario",
};

const TAB_ICONS: Record<LoginTab, React.ReactNode> = {
  dni: <IdCard className="size-4" aria-hidden="true" />,
  email: <Mail className="size-4" aria-hidden="true" />,
  username: <User className="size-4" aria-hidden="true" />,
};

// =============================================================================
// FIELDS
// =============================================================================

/**
 * The identity of the person: the DNI, the email or the username.
 *
 * The label, the icon and the error are drawn ONCE, by `FormField`.
 */
function CampoIdentidad({
  id,
  etiqueta,
  placeholder,
  icono: Icono,
  tipo = "text",
  inputMode,
  autoComplete,
  maxLength,
  registro,
  error,
}: {
  id: string;
  etiqueta: string;
  placeholder: string;
  icono: LucideIcon;
  tipo?: string;
  inputMode?: "numeric" | "email" | "text";
  autoComplete: string;
  maxLength?: number;
  registro: UseFormRegisterReturn;
  error?: string;
}) {
  return (
    <FormField
      id={id}
      label={etiqueta}
      required
      icon={Icono}
      span={12}
      error={error}
    >
      {(control) => (
        <Input
          {...control}
          {...registro}
          type={tipo}
          inputMode={inputMode}
          placeholder={placeholder}
          autoComplete={autoComplete}
          maxLength={maxLength}
        />
      )}
    </FormField>
  );
}

/**
 * The password of the access.
 *
 * It shares the toggle of the registration (`ToggleContrasena`): the same
 * icon, the same size, the same accessible name and the same motion.
 */
function CampoContrasena({
  id,
  registro,
  error,
}: {
  id: string;
  registro: UseFormRegisterReturn;
  error?: string;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <FormField
      id={id}
      label="Contraseña"
      required
      icon={KeyRound}
      span={12}
      error={error}
    >
      {(control) => (
        <div className="relative">
          <Input
            {...control}
            {...registro}
            type={visible ? "text" : "password"}
            placeholder="••••••••"
            autoComplete="current-password"
            className="pr-12"
          />
          <ToggleContrasena
            visible={visible}
            onToggle={() => setVisible((actual) => !actual)}
            campo="contraseña"
          />
        </div>
      )}
    </FormField>
  );
}

/**
 * The button of the access.
 *
 * It is the CTA of the brand: the gradient, without the sweep of light that
 * never stops.
 */
function BotonAcceso({
  pendiente,
  etiqueta,
}: {
  pendiente: boolean;
  etiqueta: string;
}) {
  return (
    <Button
      type="submit"
      disabled={pendiente}
      className="btn-brand-gradient h-14 w-full rounded-[1.5rem] text-base font-semibold"
    >
      {pendiente ? (
        <>
          <Loader2 className="size-5 animate-spin" aria-hidden="true" />
          <span>Verificando…</span>
        </>
      ) : (
        <>
          <LogIn className="size-5" aria-hidden="true" />
          <span>{etiqueta}</span>
        </>
      )}
    </Button>
  );
}

// =============================================================================
// DNI TAB FORM
// =============================================================================

function DniTabForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginDniFormData>({
    resolver: zodResolver(LoginDniFormSchema),
  });

  const onSubmit = async (data: LoginDniFormData) => {
    try {
      const result = await loginMutation.mutateAsync(data);
      setAuth(result.data);
      if (result.message) notify.success(result.message);
      router.push(await resolverDeDestino());
    } catch (error) {
      notify.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <FormGrid>
        <CampoIdentidad
          id="tab-dni"
          etiqueta="DNI"
          placeholder="12345678"
          icono={IdCard}
          inputMode="numeric"
          autoComplete="off"
          maxLength={8}
          registro={register("dni")}
          error={errors.dni?.message as string | undefined}
        />

        <CampoContrasena
          id="tab-password-dni"
          registro={register("password")}
          error={errors.password?.message as string | undefined}
        />
      </FormGrid>

      <BotonAcceso
        pendiente={isSubmitting || isLoading || loginMutation.isPending}
        etiqueta="Ingresar"
      />
    </form>
  );
}

// =============================================================================
// EMAIL TAB FORM
// =============================================================================

function EmailTabForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginEmailFormData>({
    resolver: zodResolver(LoginEmailFormSchema),
  });

  const onSubmit = async (data: LoginEmailFormData) => {
    try {
      const result = await loginMutation.mutateAsync(data);
      setAuth(result.data);
      if (result.message) notify.success(result.message);
      router.push(await resolverDeDestino());
    } catch (error) {
      notify.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <FormGrid>
        <CampoIdentidad
          id="tab-email"
          etiqueta="Email"
          placeholder="ejemplo@correo.com"
          icono={Mail}
          tipo="email"
          inputMode="email"
          autoComplete="email"
          registro={register("email")}
          error={errors.email?.message as string | undefined}
        />

        <CampoContrasena
          id="tab-password-email"
          registro={register("password")}
          error={errors.password?.message as string | undefined}
        />
      </FormGrid>

      <BotonAcceso
        pendiente={isSubmitting || isLoading || loginMutation.isPending}
        etiqueta="Ingresar"
      />
    </form>
  );
}

// =============================================================================
// USERNAME TAB FORM
// =============================================================================

function UsernameTabForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginUsernameFormData>({
    resolver: zodResolver(LoginUsernameFormSchema),
  });

  const onSubmit = async (data: LoginUsernameFormData) => {
    try {
      const result = await loginMutation.mutateAsync(data);
      setAuth(result.data);
      if (result.message) notify.success(result.message);
      router.push(await resolverDeDestino());
    } catch (error) {
      notify.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <FormGrid>
        <CampoIdentidad
          id="tab-username"
          etiqueta="Usuario"
          placeholder="juan.perez"
          icono={User}
          autoComplete="username"
          registro={register("username")}
          error={errors.username?.message as string | undefined}
        />

        <CampoContrasena
          id="tab-password-username"
          registro={register("password")}
          error={errors.password?.message as string | undefined}
        />
      </FormGrid>

      <BotonAcceso
        pendiente={isSubmitting || isLoading || loginMutation.isPending}
        etiqueta="Ingresar"
      />
    </form>
  );
}

// =============================================================================
// LOGIN SHELL
// =============================================================================

export function LoginClientShell() {
  const [activeTab, setActiveTab] = useState<LoginTab>("dni");

  return (
    <div className="login-shell">
      <AuthShell
        variant="login"
        form={<LoginBody activeTab={activeTab} setActiveTab={setActiveTab} />}
      />
    </div>
  );
}

function LoginBody({
  activeTab,
  setActiveTab,
}: {
  activeTab: LoginTab;
  setActiveTab: (t: LoginTab) => void;
}) {
  return (
    <AuthGlassCard>
      <div className="mb-8 flex flex-col items-center gap-2 text-center">
        <FestBrandHeader
          variant="onLight"
          size="md"
          subtitle="Acceso a Salesianos FEST"
        />
        <p className="mt-1 max-w-xs text-sm leading-relaxed text-muted-foreground">
          Inicia sesion para gestionar tu inscripcion, tus pagos y tu equipo.
        </p>
      </div>

      <div className="relative mb-8 flex w-full items-center rounded-full bg-muted p-1">
        <div
          className="absolute top-1 bottom-1 rounded-full bg-primary shadow-md transition-transform duration-(--motion-duration-base) ease-out"
          style={{
            width: "calc(33.333% - 4px)",
            transform: `translateX(${
              activeTab === "dni"
                ? "0"
                : activeTab === "email"
                  ? "calc(100% + 4px)"
                  : "calc(200% + 8px)"
            })`,
          }}
        />
        {TAB_ORDER.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={cn(
              "relative z-10 flex min-h-11 flex-1 items-center justify-center gap-2 rounded-full px-2 py-3 transition-colors duration-(--motion-duration-fast)",
              activeTab === tab
                ? "font-semibold text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {TAB_ICONS[tab]}
            <span className="text-xs font-semibold">{TAB_LABELS[tab]}</span>
          </button>
        ))}
      </div>

      <div>
        {activeTab === "dni" && <DniTabForm isLoading={false} />}
        {activeTab === "email" && <EmailTabForm isLoading={false} />}
        {activeTab === "username" && <UsernameTabForm isLoading={false} />}
      </div>

      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground">
          ¿No tienes cuenta?{" "}
          <Link
            href={RUTAS.auth.registro}
            className="font-semibold text-primary hover:underline"
          >
            Inscribe tu equipo
          </Link>
        </p>
      </div>

      <div className="mt-6 text-center">
        <p className="text-caption text-muted-foreground">
          Salesianos FEST — Asociacion Okinawense del Peru
        </p>
      </div>
    </AuthGlassCard>
  );
}
