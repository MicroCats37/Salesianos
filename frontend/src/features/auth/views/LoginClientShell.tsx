"use client";

import {
  Eye,
  EyeOff,
  IdCard,
  KeyRound,
  Loader2,
  LogIn,
  Mail,
  User,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { useLogin } from "@/features/auth/hooks";
import { AuthShell } from "@/features/auth/components/AuthShell";
import { AuthGlassCard } from "@/features/auth/components/AuthGlassCard";
import { handleApiError } from "@/errors/error-handler";
import {
  type LoginUsernameFormData,
  type LoginDniFormData,
  type LoginEmailFormData,
  LoginUsernameFormSchema,
  LoginDniFormSchema,
  LoginEmailFormSchema,
} from "@/features/auth/schemas";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { consumePostAuthRedirect } from "@/lib/post-auth-redirect";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { type UseFormRegisterReturn, useForm } from "react-hook-form";

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
  dni: <IdCard className="h-4 w-4" aria-hidden="true" />,
  email: <Mail className="h-4 w-4" aria-hidden="true" />,
  username: <User className="h-4 w-4" aria-hidden="true" />,
};

// =============================================================================
// PASSWORD INPUT
// =============================================================================

interface PasswordInputFieldProps {
  id: string;
  registration: UseFormRegisterReturn;
  error?: string;
}

function PasswordInputField({ id, registration, error }: PasswordInputFieldProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="space-y-1.5">
      <Label
        htmlFor={id}
        className="text-xs font-bold uppercase tracking-wider text-slate-700"
      >
        Contrasena
      </Label>
      <div className="relative">
        <KeyRound
          className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400 pointer-events-none"
          aria-hidden="true"
        />
        <Input
          id={id}
          type={showPassword ? "text" : "password"}
          placeholder="••••••••"
          autoComplete="current-password"
          className={cn(
            "input-brand pl-9 pr-10",
            error && "border-destructive ring-1 ring-destructive",
          )}
          {...registration}
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
      {error && (
        <p className="flex items-center gap-1.5 text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
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
      if (result.message) toast.success(result.message);
      const postAuth = consumePostAuthRedirect();
      router.push(postAuth ?? "/dashboard");
    } catch (error) {
      toast.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-4">
        <Label
          htmlFor="tab-dni"
          className="text-xs font-bold uppercase tracking-wider text-slate-700"
        >
          DNI
        </Label>
        <div className="relative">
          <IdCard
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
          <Input
            id="tab-dni"
            type="text"
            inputMode="numeric"
            placeholder="12345678"
            autoComplete="off"
            maxLength={8}
            className={cn(
              "input-brand pl-9",
              errors.dni?.message && "border-destructive ring-1 ring-destructive",
            )}
            {...register("dni")}
          />
        </div>
        {errors.dni && (
          <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
            {errors.dni.message as string}
          </p>
        )}
      </div>

      <PasswordInputField
        id="tab-password-dni"
        registration={register("password")}
        error={errors.password?.message as string | undefined}
      />

      <Button
        type="submit"
        disabled={isSubmitting || isLoading || loginMutation.isPending}
        className="btn-login w-full h-14 rounded-[1.5rem] text-primary-foreground font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3"
      >
        {isSubmitting || isLoading || loginMutation.isPending ? (
          <>
            <Loader2
              className="w-5 h-5 animate-spin"
              style={{ color: "var(--color-gold)" }}
              aria-hidden="true"
            />
            <span>Verificando...</span>
          </>
        ) : (
          <>
            <LogIn className="w-5 h-5" aria-hidden="true" />
            <span>Ingresar</span>
          </>
        )}
      </Button>
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
      if (result.message) toast.success(result.message);
      const postAuth = consumePostAuthRedirect();
      router.push(postAuth ?? "/dashboard");
    } catch (error) {
      toast.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-4">
        <Label
          htmlFor="tab-email"
          className="text-xs font-bold uppercase tracking-wider text-slate-700"
        >
          Email
        </Label>
        <div className="relative">
          <Mail
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
          <Input
            id="tab-email"
            type="email"
            placeholder="ejemplo@correo.com"
            autoComplete="email"
            className={cn(
              "input-brand pl-9",
              errors.email?.message && "border-destructive ring-1 ring-destructive",
            )}
            {...register("email")}
          />
        </div>
        {errors.email && (
          <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
            {errors.email.message as string}
          </p>
        )}
      </div>

      <PasswordInputField
        id="tab-password-email"
        registration={register("password")}
        error={errors.password?.message as string | undefined}
      />

      <Button
        type="submit"
        disabled={isSubmitting || isLoading || loginMutation.isPending}
        className="btn-login w-full h-14 rounded-[1.5rem] text-primary-foreground font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3"
      >
        {isSubmitting || isLoading || loginMutation.isPending ? (
          <>
            <Loader2
              className="w-5 h-5 animate-spin"
              style={{ color: "var(--color-gold)" }}
              aria-hidden="true"
            />
            <span>Verificando...</span>
          </>
        ) : (
          <>
            <LogIn className="w-5 h-5" aria-hidden="true" />
            <span>Ingresar</span>
          </>
        )}
      </Button>
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
      if (result.message) toast.success(result.message);
      const postAuth = consumePostAuthRedirect();
      router.push(postAuth ?? "/dashboard");
    } catch (error) {
      toast.error(handleApiError(error).message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-4">
        <Label
          htmlFor="tab-username"
          className="text-xs font-bold uppercase tracking-wider text-slate-700"
        >
          Usuario
        </Label>
        <div className="relative">
          <User
            className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
          <Input
            id="tab-username"
            type="text"
            placeholder="juan.perez"
            autoComplete="username"
            className={cn(
              "input-brand pl-9",
              errors.username?.message && "border-destructive ring-1 ring-destructive",
            )}
            {...register("username")}
          />
        </div>
        {errors.username && (
          <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
            {errors.username.message as string}
          </p>
        )}
      </div>

      <PasswordInputField
        id="tab-password-username"
        registration={register("password")}
        error={errors.password?.message as string | undefined}
      />

      <Button
        type="submit"
        disabled={isSubmitting || isLoading || loginMutation.isPending}
        className="btn-login w-full h-14 rounded-[1.5rem] text-primary-foreground font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3"
      >
        {isSubmitting || isLoading || loginMutation.isPending ? (
          <>
            <Loader2
              className="w-5 h-5 animate-spin"
              style={{ color: "var(--color-gold)" }}
              aria-hidden="true"
            />
            <span>Verificando...</span>
          </>
        ) : (
          <>
            <LogIn className="w-5 h-5" aria-hidden="true" />
            <span>Ingresar</span>
          </>
        )}
      </Button>
    </form>
  );
}

// =============================================================================
// LOGIN FORM PANEL — visual layout shared by AuthShell
// =============================================================================

function LoginFormBody({ activeTab }: { activeTab: LoginTab }) {
  return (
    <AuthGlassCard>
      {/* Logo + branding header */}
      <div className="mb-8 flex flex-col items-center gap-2 text-center">
        <FestBrandHeader
          variant="onLight"
          size="md"
          subtitle="Acceso para responsables de equipo"
        />
        <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500 sm:text-sm">
          Inicia sesion para revisar tu progreso, ver tus pagos pendientes y
          editar tus equipos.
        </p>
      </div>

      {/* Tab control */}
      <div className="relative flex items-center w-full bg-slate-100 p-1 rounded-full mb-8">
        <div
          className="absolute top-1 bottom-1 bg-primary rounded-full transition-all duration-300 ease-out shadow-md"
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
            onClick={() => {
              const button = document.querySelector<HTMLButtonElement>(
                `button[data-tab='${tab}']`,
              );
              button?.click();
            }}
            data-tab={tab}
            className="hidden"
            aria-hidden
          />
        ))}
        {TAB_ORDER.map((tab) => (
          <LoginTabButton key={tab} tab={tab} activeTab={activeTab} />
        ))}
      </div>

      <div className="animate-in fade-in slide-in-from-right-4 duration-200">
        {activeTab === "dni" && <DniTabForm isLoading={false} />}
        {activeTab === "email" && <EmailTabForm isLoading={false} />}
        {activeTab === "username" && <UsernameTabForm isLoading={false} />}
      </div>

      <div className="mt-8 text-center">
        <p className="text-sm text-slate-600">
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-bold text-indigo-700 hover:underline"
          >
            Inscribe tu equipo
          </Link>
        </p>
      </div>
    </AuthGlassCard>
  );
}

function LoginTabButton({
  tab,
  activeTab,
}: {
  tab: LoginTab;
  activeTab: LoginTab;
}) {
  return (
    <button
      type="button"
      data-tab-active={tab}
      onClick={() => {
        const event = new CustomEvent("auth-tab-change", {
          detail: { tab },
        });
        window.dispatchEvent(event);
      }}
      className={cn(
        "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 px-2 rounded-full transition-all duration-300",
        activeTab === tab
          ? "text-white font-bold"
          : "text-slate-600 hover:text-slate-900",
      )}
    >
      {TAB_ICONS[tab]}
      <span className="text-xs uppercase tracking-wider font-semibold">
        {TAB_LABELS[tab]}
      </span>
    </button>
  );
}

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
          subtitle="Acceso para responsables de equipo"
        />
        <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500 sm:text-sm">
          Inicia sesion para revisar tu progreso, ver tus pagos pendientes y
          editar tus equipos.
        </p>
      </div>

      <div className="relative flex items-center w-full bg-slate-100 p-1 rounded-full mb-8">
        <div
          className="absolute top-1 bottom-1 bg-primary rounded-full transition-all duration-300 ease-out shadow-md"
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
              "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 px-2 rounded-full transition-all duration-300",
              activeTab === tab
                ? "text-white font-bold"
                : "text-slate-600 hover:text-slate-900",
            )}
          >
            {TAB_ICONS[tab]}
            <span className="text-xs uppercase tracking-wider font-semibold">
              {TAB_LABELS[tab]}
            </span>
          </button>
        ))}
      </div>

      <div className="animate-in fade-in slide-in-from-right-4 duration-200">
        {activeTab === "dni" && <DniTabForm isLoading={false} />}
        {activeTab === "email" && <EmailTabForm isLoading={false} />}
        {activeTab === "username" && <UsernameTabForm isLoading={false} />}
      </div>

      <div className="mt-8 text-center">
        <p className="text-sm text-slate-600">
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-bold text-indigo-700 hover:underline"
          >
            Inscribe tu equipo
          </Link>
        </p>
      </div>

      <div className="mt-6 text-center">
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
          Salesianos FEST — Asociacion Okinawense del Peru
        </p>
      </div>
    </AuthGlassCard>
  );
}
