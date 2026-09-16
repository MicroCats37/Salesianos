/**
 * ExpedienteFormBody — campos compartidos del expediente para formularios de creación.
 *
 * Se usa en:
 * - SolicitudFormModal: datos del expediente en el modal de creación
 * - ExpedientesPage: modal de creación de expediente
 *
 * Lee los errores directamente del formState (no recibe errors por prop).
 */
"use client";

import { FileText } from "lucide-react";
import type { FieldValues, Path } from "react-hook-form";
import {
  Controller,
  type useForm,
  useFormState,
  useWatch,
} from "react-hook-form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { FormSectionHeader } from "@/components-app/forms/FormSectionHeader";

interface ExpedienteFormBodyProps<T extends FieldValues> {
  control: ReturnType<typeof useForm<T>>["control"];
}

const TIPO_DOCUMENTO_OPTIONS = [
  "OFICIO",
  "CARTA",
  "SOLICITUD",
  "MEMORANDO",
  "INFORME",
  "EXPEDIENTE",
  "RECIBO",
  "CERTIFICADO",
  "OTRO",
] as const;

export function ExpedienteFormBody<T extends FieldValues>({
  control,
}: ExpedienteFormBodyProps<T>) {
  const tipoPersona = useWatch({ control, name: "tipo_persona" as Path<T> }) as
    | "NATURAL"
    | "JURIDICA"
    | "COLEGIADO"
    | undefined;
  // Errores de formState casteados al shape simple usado en este componente
  const errors = (useFormState({ control }).errors ?? {}) as Record<
    string,
    { message?: string } | undefined
  >;

  return (
    <div className="space-y-5">
      <FormSectionHeader
        title="Datos del Solicitante"
        variant="soft"
        icon={FileText}
      />

      {/* Tipo de persona */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1 block">
            Tipo de Persona *
          </label>
          <Controller
            name={"tipo_persona" as Path<T>}
            control={control}
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger aria-invalid={!!errors.tipo_persona}>
                  <SelectValue placeholder="Seleccione..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NATURAL">Natural</SelectItem>
                  <SelectItem value="JURIDICA">Jurídica</SelectItem>
                  <SelectItem value="COLEGIADO">Colegiado</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          {errors.tipo_persona && (
            <p className="text-xs text-destructive mt-1">
              {errors.tipo_persona.message}
            </p>
          )}
        </div>

        {/* Número de documento (DNI/RUC/CIP) */}
        <div>
          <label className="text-sm font-medium mb-1 block">
            {tipoPersona === "NATURAL"
              ? "DNI *"
              : tipoPersona === "JURIDICA"
                ? "RUC *"
                : "CIP *"}
          </label>
          <Controller
            name={
              (tipoPersona === "NATURAL"
                ? "dni"
                : tipoPersona === "JURIDICA"
                  ? "ruc"
                  : "cip") as Path<T>
            }
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                value={(field.value as string) ?? ""}
                maxLength={
                  tipoPersona === "NATURAL"
                    ? 8
                    : tipoPersona === "JURIDICA"
                      ? 11
                      : 20
                }
                placeholder={
                  tipoPersona === "NATURAL"
                    ? "Ej: 12345678"
                    : tipoPersona === "JURIDICA"
                      ? "Ej: 20123456789"
                      : "Ej: 12345"
                }
                aria-invalid={!!errors.dni || !!errors.ruc || !!errors.cip}
              />
            )}
          />
          {errors.dni && (
            <p className="text-xs text-destructive mt-1">
              {errors.dni.message}
            </p>
          )}
          {errors.ruc && (
            <p className="text-xs text-destructive mt-1">
              {errors.ruc.message}
            </p>
          )}
          {errors.cip && (
            <p className="text-xs text-destructive mt-1">
              {errors.cip.message}
            </p>
          )}
        </div>
      </div>

      {/* Nombres / Razón Social */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tipoPersona === "NATURAL" ? (
          <>
            <div>
              <label className="text-sm font-medium mb-1 block">
                Nombres *
              </label>
              <Controller
                name={"nombres" as Path<T>}
                control={control}
                render={({ field }) => (
                  <Input
                    {...field}
                    value={(field.value as string) ?? ""}
                    placeholder="Nombres completos"
                    aria-invalid={!!errors.nombres}
                  />
                )}
              />
              {errors.nombres && (
                <p className="text-xs text-destructive mt-1">
                  {errors.nombres.message}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">
                Apellidos *
              </label>
              <Controller
                name={"apellidos" as Path<T>}
                control={control}
                render={({ field }) => (
                  <Input
                    {...field}
                    value={(field.value as string) ?? ""}
                    placeholder="Apellidos completos"
                    aria-invalid={!!errors.apellidos}
                  />
                )}
              />
              {errors.apellidos && (
                <p className="text-xs text-destructive mt-1">
                  {errors.apellidos.message}
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="md:col-span-2">
            <label className="text-sm font-medium mb-1 block">
              Razón Social *
            </label>
            <Controller
              name={"razon_social" as Path<T>}
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  value={(field.value as string) ?? ""}
                  placeholder="Nombre o razón social de la entidad"
                  aria-invalid={!!errors.razon_social}
                />
              )}
            />
            {errors.razon_social && (
              <p className="text-xs text-destructive mt-1">
                {errors.razon_social.message}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Contacto */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1 block">Correo</label>
          <Controller
            name={"correo" as Path<T>}
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                value={(field.value as string) ?? ""}
                type="email"
                placeholder="correo@ejemplo.com"
                aria-invalid={!!errors.correo}
              />
            )}
          />
          {errors.correo && (
            <p className="text-xs text-destructive mt-1">
              {errors.correo.message}
            </p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium mb-1 block">Teléfono</label>
          <Controller
            name={"telefono" as Path<T>}
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                value={(field.value as string) ?? ""}
                placeholder="Ej: 999 888 777"
                aria-invalid={!!errors.telefono}
              />
            )}
          />
          {errors.telefono && (
            <p className="text-xs text-destructive mt-1">
              {errors.telefono.message}
            </p>
          )}
        </div>
      </div>

      <FormSectionHeader
        title="Datos del Documento"
        variant="soft"
        icon={FileText}
      />

      {/* Tipo de documento y número */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1 block">
            Tipo de Documento *
          </label>
          <Controller
            name={"tipo_documento" as Path<T>}
            control={control}
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger aria-invalid={!!errors.tipo_documento}>
                  <SelectValue placeholder="Seleccione..." />
                </SelectTrigger>
                <SelectContent>
                  {TIPO_DOCUMENTO_OPTIONS.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.tipo_documento && (
            <p className="text-xs text-destructive mt-1">
              {errors.tipo_documento.message}
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium mb-1 block">
            Número de Documento
          </label>
          <Controller
            name={"numero_documento" as Path<T>}
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                value={(field.value as string) ?? ""}
                placeholder="Ej: 001-2024"
              />
            )}
          />
        </div>
      </div>

      {/* Folios */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1 block">
            Número de Folios
          </label>
          <Controller
            name={"numero_folios" as Path<T>}
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                value={(field.value as number) ?? 0}
                type="number"
                min={0}
                placeholder="0"
              />
            )}
          />
        </div>
      </div>

      <FormSectionHeader
        title="Descripción del Asunto"
        variant="soft"
        icon={FileText}
      />

      {/* Asunto */}
      <div>
        <label className="text-sm font-medium mb-1 block">Asunto *</label>
        <Controller
          name={"asunto" as Path<T>}
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              value={(field.value as string) ?? ""}
              placeholder="Describa el motivo de su solicitud..."
              rows={3}
              aria-invalid={!!errors.asunto}
            />
          )}
        />
        {errors.asunto && (
          <p className="text-xs text-destructive mt-1">
            {errors.asunto.message}
          </p>
        )}
      </div>

      {/* Observaciones */}
      <div>
        <label className="text-sm font-medium mb-1 block">Observaciones</label>
        <Controller
          name={"observaciones" as Path<T>}
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              value={(field.value as string) ?? ""}
              placeholder="Información adicional opcional..."
              rows={2}
            />
          )}
        />
      </div>
    </div>
  );
}
