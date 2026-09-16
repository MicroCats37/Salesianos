"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  CheckCircle2,
  Hash,
  Loader2,
  Lock,
  Mail,
  Phone,
  PhoneCall,
  User,
  UserPlus,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { handleApiError } from "@/errors/error-handler";
import { notify } from "@/errors/toast-adapter";
import { stripNonDigits } from "@/lib/utils";
import { useRegister } from "../hooks/useRegister";
import { type RegisterFormData, RegisterFormSchema } from "../schemas";

export function RegisterForm() {
  const router = useRouter();
  const registerMutation = useRegister();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(RegisterFormSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      tipoDocumento: "DNI",
      numeroDocumento: "",
      nombres: "",
      apellidos: "",
      genero: null,
      telefono: null,
      whatsapp: null,
      emergencyName: null,
      emergencyPhone: null,
      acceptedBases: false,
    },
  });

  const onSubmit = handleSubmit(async (data) => {
    setErrorMessage(null);
    try {
      await registerMutation.mutateAsync(data);
      notify.success("¡Cuenta creada con éxito!");
      router.push("/inscripcion");
      router.refresh();
    } catch (error) {
      handleApiError(error);
      setErrorMessage((error as Error).message);
    }
  });

  return (
    <Card className="card-elevated w-full max-w-xl mx-auto overflow-hidden border-0 shadow-2xl">
      <div className="bg-gradient-to-br from-[#f4c64e] to-[#d8a93a] px-6 py-8 text-center text-[#17214b]">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/40 backdrop-blur">
          <UserPlus className="size-8" />
        </div>
        <CardTitle className="text-2xl font-black">Crear cuenta</CardTitle>
        <CardDescription className="mt-2 text-[#17214b]/85">
          Únete y preinscribe a tu promoción en Salesianos FEST 2026.
        </CardDescription>
      </div>

      <form id="register-form" onSubmit={onSubmit} noValidate>
        <CardContent className="space-y-5 p-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="size-4 text-[#312e8e]" /> Email
            </Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="tu@email.com"
              className="input-brand"
              {...register("email")}
              aria-invalid={!!errors.email}
            />
            {errors.email && (
              <p className="flex items-center gap-1.5 text-sm text-destructive">
                <AlertCircle className="size-4" /> {errors.email.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="password" className="flex items-center gap-2">
                <Lock className="size-4 text-[#312e8e]" /> Contraseña
              </Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                placeholder="Mín. 8 caracteres"
                className="input-brand"
                {...register("password")}
                aria-invalid={!!errors.password}
              />
              {errors.password && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" /> {errors.password.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label
                htmlFor="confirmPassword"
                className="flex items-center gap-2"
              >
                <CheckCircle2 className="size-4 text-[#312e8e]" /> Confirmar
              </Label>
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                placeholder="Repite"
                className="input-brand"
                {...register("confirmPassword")}
                aria-invalid={!!errors.confirmPassword}
              />
              {errors.confirmPassword && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" />{" "}
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label
                htmlFor="tipoDocumento"
                className="flex items-center gap-2"
              >
                <Hash className="size-4 text-[#312e8e]" /> Tipo de documento
              </Label>
              <Select
                defaultValue="DNI"
                onValueChange={(val) =>
                  setValue("tipoDocumento", val as "DNI" | "CE" | "PAS")
                }
                {...register("tipoDocumento")}
              >
                <SelectTrigger className="input-brand">
                  <SelectValue placeholder="Selecciona tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DNI">DNI</SelectItem>
                  <SelectItem value="CE">CE</SelectItem>
                  <SelectItem value="PAS">PAS</SelectItem>
                </SelectContent>
              </Select>
              {errors.tipoDocumento && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" />{" "}
                  {errors.tipoDocumento.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label
                htmlFor="numeroDocumento"
                className="flex items-center gap-2"
              >
                <Hash className="size-4 text-[#312e8e]" /> Número de documento
              </Label>
              {(() => {
                const { onChange, ...rest } = register("numeroDocumento");
                return (
                  <Input
                    id="numeroDocumento"
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="12345678"
                    className="input-brand"
                    maxLength={20}
                    {...rest}
                    onChange={(e) => {
                      const currentTipo = watch("tipoDocumento");
                      let filtered: string;
                      let maxLen: number;
                      if (currentTipo === "PAS") {
                        // PAS is alphanumeric — strip only special chars
                        filtered = e.target.value.replace(/[^a-zA-Z0-9]/g, "");
                        maxLen = 20;
                      } else if (currentTipo === "CE") {
                        // CE must be exactly 9 numeric digits
                        filtered = stripNonDigits(e.target.value).slice(0, 9);
                        maxLen = 9;
                      } else {
                        // DNI must be exactly 8 numeric digits
                        filtered = stripNonDigits(e.target.value).slice(0, 8);
                        maxLen = 8;
                      }
                      e.target.value = filtered;
                      // Dynamically enforce maxLength per document type
                      if (filtered.length > maxLen) {
                        e.target.value = filtered.slice(0, maxLen);
                      }
                      onChange(e);
                    }}
                    aria-invalid={!!errors.numeroDocumento}
                  />
                );
              })()}
              {errors.numeroDocumento && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" />{" "}
                  {errors.numeroDocumento.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="nombres" className="flex items-center gap-2">
                <User className="size-4 text-[#312e8e]" /> Nombres
              </Label>
              <Input
                id="nombres"
                type="text"
                autoComplete="given-name"
                placeholder="Juan Carlos"
                className="input-brand"
                {...register("nombres")}
                aria-invalid={!!errors.nombres}
              />
              {errors.nombres && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" /> {errors.nombres.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="apellidos" className="flex items-center gap-2">
                <User className="size-4 text-[#312e8e]" /> Apellidos
              </Label>
              <Input
                id="apellidos"
                type="text"
                autoComplete="family-name"
                placeholder="Pérez López"
                className="input-brand"
                {...register("apellidos")}
                aria-invalid={!!errors.apellidos}
              />
              {errors.apellidos && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" /> {errors.apellidos.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="genero" className="flex items-center gap-2">
                <User className="size-4 text-[#312e8e]" /> Género
              </Label>
              <Select
                onValueChange={(val) =>
                  setValue("genero", val as "V" | "M" | null)
                }
                {...register("genero")}
              >
                <SelectTrigger className="input-brand">
                  <SelectValue placeholder="Opcional" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="V">Masculino</SelectItem>
                  <SelectItem value="M">Femenino</SelectItem>
                </SelectContent>
              </Select>
              {errors.genero && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" /> {errors.genero.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="telefono" className="flex items-center gap-2">
                <Phone className="size-4 text-[#312e8e]" /> Teléfono
              </Label>
              {(() => {
                const { onChange, ...rest } = register("telefono");
                return (
                  <Input
                    id="telefono"
                    type="tel"
                    inputMode="numeric"
                    autoComplete="tel"
                    maxLength={9}
                    placeholder="987654321 (opcional)"
                    className="input-brand"
                    {...rest}
                    onChange={(e) => {
                      const filtered = stripNonDigits(e.target.value).slice(
                        0,
                        9,
                      );
                      e.target.value = filtered;
                      onChange(e);
                    }}
                    aria-invalid={!!errors.telefono}
                  />
                );
              })()}
              {errors.telefono && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" /> {errors.telefono.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="whatsapp" className="flex items-center gap-2">
              <Phone className="size-4 text-[#312e8e]" /> WhatsApp
            </Label>
            {(() => {
              const { onChange, ...rest } = register("whatsapp");
              return (
                <Input
                  id="whatsapp"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel"
                  maxLength={9}
                  placeholder="987654321 (opcional)"
                  className="input-brand"
                  {...rest}
                  onChange={(e) => {
                    const filtered = stripNonDigits(e.target.value).slice(0, 9);
                    e.target.value = filtered;
                    onChange(e);
                  }}
                  aria-invalid={!!errors.whatsapp}
                />
              );
            })()}
            {errors.whatsapp && (
              <p className="flex items-center gap-1.5 text-sm text-destructive">
                <AlertCircle className="size-4" /> {errors.whatsapp.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label
                htmlFor="emergencyName"
                className="flex items-center gap-2"
              >
                <PhoneCall className="size-4 text-[#312e8e]" /> Contacto de
                emergencia
              </Label>
              <Input
                id="emergencyName"
                placeholder="Nombre y apellido (opcional)"
                className="input-brand"
                {...register("emergencyName")}
                aria-invalid={!!errors.emergencyName}
              />
              {errors.emergencyName && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" />{" "}
                  {errors.emergencyName.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label
                htmlFor="emergencyPhone"
                className="flex items-center gap-2"
              >
                <PhoneCall className="size-4 text-[#312e8e]" /> Tel. emergencia
              </Label>
              {(() => {
                const { onChange, ...rest } = register("emergencyPhone");
                return (
                  <Input
                    id="emergencyPhone"
                    type="tel"
                    inputMode="numeric"
                    maxLength={9}
                    placeholder="999 999 999 (opcional)"
                    className="input-brand"
                    {...rest}
                    onChange={(e) => {
                      const filtered = stripNonDigits(e.target.value).slice(
                        0,
                        9,
                      );
                      e.target.value = filtered;
                      onChange(e);
                    }}
                    aria-invalid={!!errors.emergencyPhone}
                  />
                );
              })()}
              {errors.emergencyPhone && (
                <p className="flex items-center gap-1.5 text-sm text-destructive">
                  <AlertCircle className="size-4" />{" "}
                  {errors.emergencyPhone.message}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-xl border-2 border-[#f4c64e]/40 bg-[#fff9df] p-4">
            <Checkbox
              id="acceptedBases"
              checked={watch("acceptedBases")}
              onCheckedChange={(checked) =>
                setValue("acceptedBases", !!checked)
              }
              aria-invalid={!!errors.acceptedBases}
              className="mt-0.5"
            />
            <div>
              <Label
                htmlFor="acceptedBases"
                className="cursor-pointer font-bold leading-tight text-[#17214b]"
              >
                Acepto las bases oficiales del evento
              </Label>
              <p className="mt-1 text-xs text-muted-foreground">
                He leído y acepto los términos del documento{" "}
                <strong>BASES-SF26-2026-09-06</strong>.
              </p>
            </div>
          </div>
          {errors.acceptedBases && (
            <p className="flex items-center gap-1.5 text-sm text-destructive">
              <AlertCircle className="size-4" /> {errors.acceptedBases.message}
            </p>
          )}

          {errorMessage && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="size-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}
        </CardContent>
      </form>

      <div className="flex flex-col gap-3 border-t border-border/60 p-6 pt-5">
        <Button
          type="submit"
          form="register-form"
          disabled={registerMutation.isPending}
          className="btn-brand-gradient btn-shine h-12 rounded-xl text-base font-black uppercase tracking-wider"
        >
          {registerMutation.isPending ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" /> Creando cuenta...
            </>
          ) : (
            "Crear cuenta"
          )}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-bold text-[#312e8e] underline-offset-4 hover:underline"
          >
            Inicia sesión
          </Link>
        </p>
      </div>
    </Card>
  );
}
