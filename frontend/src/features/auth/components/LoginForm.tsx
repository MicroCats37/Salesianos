"use client";

import {
  AlertCircle,
  Eye,
  EyeOff,
  IdCard,
  Loader2,
  Lock,
  LogIn,
  Mail,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/features/auth/hooks/useLogin";
import {
  type LoginDniFormData,
  LoginDniFormSchema,
  type LoginEmailFormData,
  LoginEmailFormSchema,
} from "@/features/auth/schemas";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { cn } from "@/lib/utils";

// ── Tab Types ──────────────────────────────────────────────────────────────────

type LoginTab = "dni" | "email";

// ── Password Field Component ───────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFormMethods = ReturnType<typeof import("react-hook-form").useForm<any>>;

interface PasswordFieldProps {
  methods: AnyFormMethods;
}

function PasswordField({ methods }: PasswordFieldProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="space-y-2">
      <Label htmlFor="password" className="flex items-center gap-2">
        <Lock className="size-4 text-[#312e8e]" /> Contraseña
      </Label>
      <div className="relative">
        <Input
          id="password"
          type={showPassword ? "text" : "password"}
          autoComplete="current-password"
          placeholder="••••••••"
          className="input-brand pr-12"
          {...methods.register("password")}
          aria-invalid={!!methods.formState.errors.password}
        />
        <button
          type="button"
          onClick={() => setShowPassword((value) => !value)}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-[#312e8e]"
          aria-label={
            showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
          }
        >
          {showPassword ? (
            <EyeOff className="size-4" />
          ) : (
            <Eye className="size-4" />
          )}
        </button>
      </div>
      {methods.formState.errors.password && (
        <p className="flex items-center gap-1.5 text-sm text-destructive">
          <AlertCircle className="size-4" />
          {methods.formState.errors.password.message as string}
        </p>
      )}
    </div>
  );
}

// ── Sub-Forms ─────────────────────────────────────────────────────────────────

function DniLoginForm({ onSuccess }: { onSuccess: (user: unknown) => void }) {
  const loginMutation = useLogin();

  return (
    <GenericForm<LoginDniFormData>
      schema={LoginDniFormSchema}
      submitButtonText="Ingresar"
      isLoading={loginMutation.isPending}
      onSubmit={async (data) => {
        const user = await loginMutation.mutateAsync(data);
        onSuccess(user);
      }}
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <div className="space-y-5">
          {submissionMessage?.type === "error" && (
            <p className="flex items-center gap-1.5 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="size-4" />
              {submissionMessage.message}
            </p>
          )}

          <div className="space-y-2">
            <Label htmlFor="dni" className="flex items-center gap-2">
              <IdCard className="size-4 text-[#312e8e]" /> DNI
            </Label>
            {(() => {
              const { onChange, ...rest } = methods.register("dni");
              return (
                <Input
                  id="dni"
                  type="text"
                  inputMode="numeric"
                  autoComplete="off"
                  placeholder="Ej: 12345678"
                  maxLength={8}
                  className="input-brand"
                  {...rest}
                  onChange={(e) => {
                    const filtered = e.target.value
                      .replace(/\D/g, "")
                      .slice(0, 8);
                    e.target.value = filtered;
                    onChange(e);
                  }}
                  aria-invalid={!!methods.formState.errors.dni}
                />
              );
            })()}
            {methods.formState.errors.dni && (
              <p className="flex items-center gap-1.5 text-sm text-destructive">
                <AlertCircle className="size-4" />
                {methods.formState.errors.dni.message as string}
              </p>
            )}
          </div>

          <PasswordField methods={methods} />

          <Button
            type="submit"
            disabled={isSubmitting}
            className="btn-brand-gradient btn-shine h-12 w-full rounded-xl text-base font-black uppercase tracking-wider"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Verificando...
              </>
            ) : (
              "Ingresar"
            )}
          </Button>
        </div>
      )}
    </GenericForm>
  );
}

function EmailLoginForm({ onSuccess }: { onSuccess: (user: unknown) => void }) {
  const loginMutation = useLogin();

  return (
    <GenericForm<LoginEmailFormData>
      schema={LoginEmailFormSchema}
      submitButtonText="Ingresar"
      isLoading={loginMutation.isPending}
      onSubmit={async (data) => {
        const user = await loginMutation.mutateAsync(data);
        onSuccess(user);
      }}
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <div className="space-y-5">
          {submissionMessage?.type === "error" && (
            <p className="flex items-center gap-1.5 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="size-4" />
              {submissionMessage.message}
            </p>
          )}

          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="size-4 text-[#312e8e]" /> Correo electrónico
            </Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="Ej: usuario@ejemplo.com"
              className="input-brand"
              {...methods.register("email")}
              aria-invalid={!!methods.formState.errors.email}
            />
            {methods.formState.errors.email && (
              <p className="flex items-center gap-1.5 text-sm text-destructive">
                <AlertCircle className="size-4" />
                {methods.formState.errors.email.message as string}
              </p>
            )}
          </div>

          <PasswordField methods={methods} />

          <Button
            type="submit"
            disabled={isSubmitting}
            className="btn-brand-gradient btn-shine h-12 w-full rounded-xl text-base font-black uppercase tracking-wider"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Verificando...
              </>
            ) : (
              "Ingresar"
            )}
          </Button>
        </div>
      )}
    </GenericForm>
  );
}

// ── Main LoginForm with Tabs ───────────────────────────────────────────────────

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setUser = useAuthStore((s) => s.setUser);
  const [activeTab, setActiveTab] = useState<LoginTab>("dni");
  const [error, setError] = useState<string | null>(null);

  const handleSuccess = (user: unknown) => {
    setUser(user as ReturnType<typeof useAuthStore.getState>["user"]);
    toast.success("¡Bienvenido de vuelta!");

    const explicitRedirect = searchParams.get("redirect");
    if (explicitRedirect) {
      router.push(explicitRedirect);
    } else {
      const u = user as { rol?: string };
      if (u.rol === "admin_comite" || u.rol === "admin_finanzas") {
        router.push("/admin/dashboard");
      } else {
        router.push("/dashboard");
      }
    }
    router.refresh();
  };

  return (
    <Card className="card-elevated w-full max-w-md mx-auto overflow-hidden border-0 shadow-2xl">
      {/* Header */}
      <div className="bg-gradient-to-br from-[#312e8e] to-[#25236f] px-6 py-8 text-center text-white">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
          <LogIn className="size-8" />
        </div>
        <CardTitle className="text-2xl font-black text-white">
          Iniciar sesión
        </CardTitle>
        <CardDescription className="mt-2 text-white/85">
          Accede con tu DNI o correo electrónico.
        </CardDescription>
      </div>

      <CardContent className="space-y-5 p-6">
        {/* Error message */}
        {error && (
          <p className="flex items-center gap-1.5 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            <AlertCircle className="size-4" />
            {error}
          </p>
        )}

        {/* Segmented Tab Control */}
        <div className="relative flex items-center w-full bg-muted/60 p-1 rounded-full">
          {/* Active indicator */}
          <div
            className="absolute top-1 bottom-1 bg-primary rounded-full transition-all duration-300 ease-out"
            style={{
              width: "calc(50% - 4px)",
              transform: `translateX(${
                activeTab === "dni" ? "0" : "calc(100% + 4px)"
              })`,
            }}
          />

          {/* DNI Tab */}
          <button
            type="button"
            onClick={() => {
              setActiveTab("dni");
              setError(null);
            }}
            className={cn(
              "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full transition-all duration-300",
              activeTab === "dni"
                ? "text-primary-foreground font-bold"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <IdCard className="h-4 w-4" aria-hidden="true" />
            <span className="text-xs uppercase tracking-wider font-semibold">
              DNI
            </span>
          </button>

          {/* Email Tab */}
          <button
            type="button"
            onClick={() => {
              setActiveTab("email");
              setError(null);
            }}
            className={cn(
              "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full transition-all duration-300",
              activeTab === "email"
                ? "text-primary-foreground font-bold"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Mail className="h-4 w-4" aria-hidden="true" />
            <span className="text-xs uppercase tracking-wider font-semibold">
              Email
            </span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="animate-in fade-in slide-in-from-right-4 duration-200">
          {activeTab === "dni" && <DniLoginForm onSuccess={handleSuccess} />}
          {activeTab === "email" && (
            <EmailLoginForm onSuccess={handleSuccess} />
          )}
        </div>
      </CardContent>

      <div className="flex flex-col gap-3 border-t border-border/60 p-6 pt-5">
        <p className="text-center text-sm text-muted-foreground">
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-bold text-[#312e8e] underline-offset-4 hover:underline"
          >
            Regístrate aquí
          </Link>
        </p>
      </div>
    </Card>
  );
}
