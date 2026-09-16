"use client";

import {
  Eye,
  EyeOff,
  IdCard,
  KeyRound,
  Loader2,
  Mail,
  User,
} from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/features/auth/hooks/useLogin";
import {
  type LoginDniFormData,
  LoginDniFormSchema,
  type LoginEmailFormData,
  LoginEmailFormSchema,
  type LoginUsernameFormData,
  LoginUsernameFormSchema,
} from "@/features/auth/schemas";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { cn } from "@/lib/utils";

// =============================================================================
// SUB-FORM: Username Login
// =============================================================================
function UsernameLoginForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <GenericForm<LoginUsernameFormData>
      schema={LoginUsernameFormSchema}
      submitButtonText="Ingresar"
      isLoading={isLoading || loginMutation.isPending}
      onSubmit={async (data) => {
        try {
          const auth = await loginMutation.mutateAsync(data);
          setAuth(auth);
          toast.success("Bienvenido a Mesa de Partes");
          router.push("/solicitudes");
        } catch (error) {
          toast.error(
            error instanceof Error
              ? error.message
              : "Error al iniciar sesión. Verifica tus credenciales.",
          );
        }
      }}
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <div className="space-y-6">
          {/* Error message */}
          {submissionMessage && submissionMessage.type === "error" && (
            <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-bold uppercase tracking-widest animate-in fade-in slide-in-from-top-2 text-center">
              {submissionMessage.message}
            </div>
          )}

          {/* Username field */}
          <div className="space-y-3">
            <Label
              htmlFor="username"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              Usuario
            </Label>
            <div className="relative group">
              <User
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="username"
                type="text"
                placeholder="Ej: juan.perez"
                autoComplete="username"
                className={cn(
                  "h-14 pl-13 pr-5 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("username")}
              />
            </div>
            {methods.formState.errors.username && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.username.message as string}
              </p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-3">
            <Label
              htmlFor="password-username"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              Contraseña
            </Label>
            <div className="relative group">
              <KeyRound
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="password-username"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                autoComplete="current-password"
                className={cn(
                  "h-14 pl-13 pr-14 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors p-1"
                aria-label={
                  showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                }
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Eye className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
            {methods.formState.errors.password && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.password.message as string}
              </p>
            )}
          </div>

          {/* Submit button */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className={cn(
              "w-full h-14 rounded-[1.5rem] btn-wine-gradient-hover text-primary-foreground font-black text-sm uppercase tracking-widest",
              "flex items-center justify-center gap-3",
            )}
          >
            {isSubmitting ? (
              <>
                <Loader2
                  className="w-5 h-5 animate-spin text-accent"
                  aria-hidden="true"
                />
                <span>Verificando...</span>
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

// =============================================================================
// SUB-FORM: DNI Login
// =============================================================================
function DniLoginForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <GenericForm<LoginDniFormData>
      schema={LoginDniFormSchema}
      submitButtonText="Ingresar"
      isLoading={isLoading || loginMutation.isPending}
      onSubmit={async (data) => {
        try {
          const auth = await loginMutation.mutateAsync(data);
          setAuth(auth);
          toast.success("Bienvenido a Mesa de Partes");
          router.push("/solicitudes");
        } catch (error) {
          toast.error(
            error instanceof Error
              ? error.message
              : "Error al iniciar sesión. Verifica tus credenciales.",
          );
        }
      }}
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <div className="space-y-6">
          {/* Error message */}
          {submissionMessage && submissionMessage.type === "error" && (
            <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-bold uppercase tracking-widest animate-in fade-in slide-in-from-top-2 text-center">
              {submissionMessage.message}
            </div>
          )}

          {/* DNI field */}
          <div className="space-y-3">
            <Label
              htmlFor="dni"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              DNI
            </Label>
            <div className="relative group">
              <IdCard
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="dni"
                type="text"
                placeholder="Ej: 12345678"
                autoComplete="off"
                maxLength={8}
                className={cn(
                  "h-14 pl-13 pr-5 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("dni")}
              />
            </div>
            {methods.formState.errors.dni && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.dni.message as string}
              </p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-3">
            <Label
              htmlFor="password-dni"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              Contraseña
            </Label>
            <div className="relative group">
              <KeyRound
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="password-dni"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                autoComplete="current-password"
                className={cn(
                  "h-14 pl-13 pr-14 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors p-1"
                aria-label={
                  showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                }
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Eye className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
            {methods.formState.errors.password && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.password.message as string}
              </p>
            )}
          </div>

          {/* Submit button */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className={cn(
              "w-full h-14 rounded-[1.5rem] btn-wine-gradient-hover text-primary-foreground font-black text-sm uppercase tracking-widest",
              "flex items-center justify-center gap-3",
            )}
          >
            {isSubmitting ? (
              <>
                <Loader2
                  className="w-5 h-5 animate-spin text-accent"
                  aria-hidden="true"
                />
                <span>Verificando...</span>
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

// =============================================================================
// SUB-FORM: Email Login
// =============================================================================
function EmailLoginForm({ isLoading }: { isLoading: boolean }) {
  const loginMutation = useLogin();
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <GenericForm<LoginEmailFormData>
      schema={LoginEmailFormSchema}
      submitButtonText="Ingresar"
      isLoading={isLoading || loginMutation.isPending}
      onSubmit={async (data) => {
        try {
          const auth = await loginMutation.mutateAsync(data);
          setAuth(auth);
          toast.success("Bienvenido a Mesa de Partes");
          router.push("/solicitudes");
        } catch (error) {
          toast.error(
            error instanceof Error
              ? error.message
              : "Error al iniciar sesión. Verifica tus credenciales.",
          );
        }
      }}
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <div className="space-y-6">
          {/* Error message */}
          {submissionMessage && submissionMessage.type === "error" && (
            <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-bold uppercase tracking-widest animate-in fade-in slide-in-from-top-2 text-center">
              {submissionMessage.message}
            </div>
          )}

          {/* Email field */}
          <div className="space-y-3">
            <Label
              htmlFor="email"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              Correo electrónico
            </Label>
            <div className="relative group">
              <Mail
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="email"
                type="email"
                placeholder="Ej: usuario@ejemplo.com"
                autoComplete="email"
                className={cn(
                  "h-14 pl-13 pr-5 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("email")}
              />
            </div>
            {methods.formState.errors.email && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.email.message as string}
              </p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-3">
            <Label
              htmlFor="password-email"
              className="text-[10px] font-black text-primary uppercase tracking-[0.2em] ml-1 block"
            >
              Contraseña
            </Label>
            <div className="relative group">
              <KeyRound
                className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors duration-300"
                aria-hidden="true"
              />
              <Input
                id="password-email"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                autoComplete="current-password"
                className={cn(
                  "h-14 pl-13 pr-14 rounded-[1.5rem] border-border bg-card text-base font-bold placeholder:text-muted-foreground/60",
                  "focus:ring-[6px] focus:ring-primary/10 focus:border-primary transition-all",
                )}
                {...methods.register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors p-1"
                aria-label={
                  showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                }
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Eye className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
            {methods.formState.errors.password && (
              <p className="text-[11px] font-bold text-destructive uppercase tracking-tight px-1 animate-in fade-in slide-in-from-top-1">
                {methods.formState.errors.password.message as string}
              </p>
            )}
          </div>

          {/* Submit button */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className={cn(
              "w-full h-14 rounded-[1.5rem] btn-wine-gradient-hover text-primary-foreground font-black text-sm uppercase tracking-widest",
              "flex items-center justify-center gap-3",
            )}
          >
            {isSubmitting ? (
              <>
                <Loader2
                  className="w-5 h-5 animate-spin text-accent"
                  aria-hidden="true"
                />
                <span>Verificando...</span>
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

// =============================================================================
// AUTH CARD WRAPPER
// =============================================================================
interface AuthCardProps {
  children: React.ReactNode;
  className?: string;
}

function AuthCard({ children, className = "" }: AuthCardProps) {
  return (
    <div
      className={cn(
        "w-full bg-card/95 backdrop-blur-sm rounded-[2rem]",
        "shadow-2xl shadow-black/20",
        "border border-primary/[0.06]" /* brand-tinted border */,
        "p-6 sm:p-8 md:p-10",
        "transition-all duration-500",
        "ring-1 ring-inset ring-primary/5" /* subtle primary glow ring */,
        className,
      )}
    >
      {children}
    </div>
  );
}

// =============================================================================
// CLIENT SHELL — Mesa de Partes Split-Screen Corporate Login
// Left: Brand panel with CIP styling
// Right: Login form with 3-Tab Segmented Control
// =============================================================================
type LoginTab = "username" | "dni" | "email";

export function LoginClientShell() {
  const [activeTab, setActiveTab] = useState<LoginTab>("username");

  return (
    <div className="min-h-screen w-full flex">
      {/* ─── LEFT PANEL: Brand / Informational ─── */}
      {/* Hidden on mobile, visible from md (tablet) up */}
      <div className="hidden md:flex md:w-1/2 lg:w-[45%] login-animated-bg relative flex-col justify-between p-8 lg:p-12">
        {/* Subtle overlay for depth */}
        <div className="absolute inset-0 bg-black/10 pointer-events-none" />

        {/* Top: Logo + Brand — prominent glass lockup */}
        <div className="relative z-10 animate-in fade-in slide-in-from-top-4 duration-700">
          <div className="flex flex-col items-center gap-3">
            {/* Logo with glass ring glow */}
            <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl shadow-2xl">
              {/* Outer glow ring */}
              <div
                className="absolute inset-0 rounded-2xl bg-white/10 backdrop-blur-md shadow-2xl"
                aria-hidden="true"
              />
              {/* Inner ring accent */}
              <div
                className="absolute inset-[3px] rounded-[14px] bg-white/5 backdrop-blur-sm border border-white/10"
                aria-hidden="true"
              />
              {/* Logo image */}
              <Image
                src="/images/logo.png"
                alt="CIP"
                width={80}
                height={80}
                className="relative z-10 h-[68px] w-[68px] object-contain"
              />
            </div>
            {/* Text below logo, centered */}
            <div className="text-center">
              <p className="text-sm font-black uppercase tracking-widest text-white/90">
                Colegio de Ingenieros del Perú
              </p>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-white/60">
                Consejo Nacional
              </p>
            </div>
          </div>
        </div>

        {/* Center: Main brand message */}
        <div className="relative z-10 flex flex-col items-center justify-center flex-1 py-12 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200">
          {/* Floating decorative accent circles — decorative only */}
          <div className="relative w-full max-w-sm" aria-hidden="true">
            {/* Top-right floating dot */}
            <div
              className="absolute -top-4 right-8 h-3 w-3 rounded-full bg-white/10 animate-cip-float"
              style={{ animationDelay: "0s" }}
            />
            {/* Left mid dot */}
            <div className="absolute top-1/3 -left-6 h-2 w-2 rounded-full bg-white/8" />
            {/* Right accent orb */}
            <div className="absolute -top-8 right-16 h-6 w-6 rounded-full bg-accent/20 backdrop-blur-sm shadow-xl shadow-accent/10" />
            {/* Bottom-left floating dot */}
            <div
              className="absolute -bottom-2 left-12 h-4 w-4 rounded-full bg-white/8 animate-cip-float"
              style={{ animationDelay: "2s" }}
            />

            {/* Main headline — large and bold */}
            <div className="text-center space-y-3">
              <h1 className="text-5xl lg:text-6xl font-black text-white tracking-tight leading-none">
                Trámite
                <br />
                Documentario
              </h1>
              <div className="flex items-center justify-center gap-2">
                <div className="h-px w-8 bg-gradient-to-r from-transparent to-accent/60" />
                <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/50">
                  CIP Consejo Nacional
                </p>
                <div className="h-px w-8 bg-gradient-to-l from-transparent to-accent/60" />
              </div>
              <p className="text-white/60 text-sm font-medium leading-relaxed max-w-xs mx-auto pt-1">
                Gestión documental integral para el Colegio de Ingenieros del
                Perú
              </p>
            </div>

            {/* Feature highlights — compact pill row */}
            <div className="flex flex-wrap justify-center gap-2 pt-6">
              <div className="flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-white/80 backdrop-blur-sm">
                <svg
                  className="h-3 w-3 text-accent flex-shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <polyline points="20,6 9,17 4,12" />
                </svg>
                Expedientes
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-white/80 backdrop-blur-sm">
                <svg
                  className="h-3 w-3 text-accent flex-shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <polyline points="20,6 9,17 4,12" />
                </svg>
                Trámites
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-white/80 backdrop-blur-sm">
                <svg
                  className="h-3 w-3 text-accent flex-shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <polyline points="20,6 9,17 4,12" />
                </svg>
                Solicitudes
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: Footer */}
        <div className="relative z-10 animate-in fade-in duration-700 delay-300">
          <div className="divider-campestre mb-4" />
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">
            Mesa de Partes — Colegio de Ingenieros del Perú
          </p>
        </div>
      </div>

      {/* ─── RIGHT PANEL: Login Form ─── */}
      <div className="flex w-full md:w-1/2 lg:w-[55%] items-center justify-center bg-background p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md animate-in fade-in zoom-in-95 duration-500">
          {/* Mobile logo — only shown on small screens */}
          <div className="md:hidden mb-8 text-center animate-in fade-in slide-in-from-top-4 duration-700">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-primary/10 mb-3">
              <Image
                src="/images/logo.png"
                alt="CIP"
                width={64}
                height={64}
                className="h-14 w-14 object-contain"
              />
            </div>
            <h1 className="text-xl font-black text-primary tracking-tight">
              Mesa de Partes
            </h1>
            <p className="text-xs text-muted-foreground font-medium">
              Colegio de Ingenieros del Perú
            </p>
          </div>

          <AuthCard>
            {/* Form Header */}
            <div className="mb-6">
              <h2 className="text-xl font-bold text-foreground tracking-tight">
                Iniciar Sesión
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Ingresa tus credenciales para continuar
              </p>
            </div>

            {/* Segmented Control — Mobile Pill Style */}
            <div className="w-full mb-6">
              <div className="relative flex items-center w-full bg-muted/60 p-1 rounded-full">
                {/* Sliding active indicator */}
                <div
                  className="absolute top-1 bottom-1 bg-primary rounded-full transition-all duration-300 ease-out"
                  style={{
                    width: "calc(33.333% - 4px)",
                    transform: `translateX(${activeTab === "username" ? "0" : activeTab === "dni" ? "calc(100% + 4px)" : "calc(200% + 8px)"})`,
                  }}
                />

                {/* Username Tab */}
                <button
                  type="button"
                  onClick={() => setActiveTab("username")}
                  className={cn(
                    "relative z-10 flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-full transition-all duration-300",
                    activeTab === "username"
                      ? "text-primary-foreground font-bold"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  <User className="h-4 w-4" aria-hidden="true" />
                  <span className="text-xs uppercase tracking-wider font-semibold">
                    Usuario
                  </span>
                </button>

                {/* DNI Tab */}
                <button
                  type="button"
                  onClick={() => setActiveTab("dni")}
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
                  onClick={() => setActiveTab("email")}
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
            </div>

            {/* Tab Content */}
            <div className="animate-in fade-in slide-in-from-right-4 duration-200">
              {activeTab === "username" && (
                <UsernameLoginForm isLoading={false} />
              )}
              {activeTab === "dni" && <DniLoginForm isLoading={false} />}
              {activeTab === "email" && <EmailLoginForm isLoading={false} />}
            </div>
          </AuthCard>

          {/* Mobile footer */}
          <div className="mt-6 text-center md:hidden">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">
              Mesa de Partes — Colegio de Ingenieros del Perú
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
