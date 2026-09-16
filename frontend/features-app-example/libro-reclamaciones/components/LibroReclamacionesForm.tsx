"use client";

import {
  AlertCircle,
  AlertTriangle,
  BookOpen,
  Building2,
  CheckCircle2,
  ClipboardList,
  FileText,
  ShieldCheck,
  User,
} from "lucide-react";
import { useCallback, useId, useMemo } from "react";
import type { UseFormReturn } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  MultiPartFormStepper,
  type PartFormConfig,
} from "@/components-app/forms/MultiPartFormStepper";
import { notify } from "@/errors";
import { cn } from "@/lib/utils";
import {
  BIEN_RECLAMADO_DEFAULTS,
  type BienReclamadoFormData,
  BienReclamadoSchema,
  DATOS_RECLAMANTE_DEFAULTS,
  type DatosReclamanteFormData,
  DatosReclamanteSchema,
  DETALLE_RECLAMACION_DEFAULTS,
  type DetalleReclamacionFormData,
  DetalleReclamacionSchema,
} from "../schemas";
import { useLibroReclamacionesUIStore } from "../store";

// ── Field wrapper ─────────────────────────────────────────────────────────────

interface StepFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  className?: string;
  fullWidth?: boolean;
}

function StepField({
  label,
  required,
  error,
  children,
  className = "",
  fullWidth = false,
}: StepFieldProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1.5",
        fullWidth ? "md:col-span-2" : "",
        className,
      )}
    >
      <Label htmlFor={label} className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive ml-0.5">*</span>}
      </Label>
      {children}
      {error && (
        <p className="text-xs text-destructive flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
}

// ── Options ────────────────────────────────────────────────────────────────────

const TIPO_DOCUMENTO_OPTIONS = [
  { label: "DNI", value: "DNI" },
  { label: "CE (Carné de Extranjería)", value: "CE" },
] as const;

const TIPO_BIEN_OPTIONS = [
  { label: "Producto", value: "PRODUCTO" },
  { label: "Servicio", value: "SERVICIO" },
] as const;

const TIPO_RECLAMACION_OPTIONS = [
  { label: "Reclamo", value: "RECLAMO" },
  { label: "Queja", value: "QUEJA" },
] as const;

// ── Step 1: Datos del Reclamante ─────────────────────────────────────────────

interface Step1RenderProps {
  methods: UseFormReturn<DatosReclamanteFormData>;
  aggregate: Record<string, unknown>;
  setValue: UseFormReturn<DatosReclamanteFormData>["setValue"];
  reset: UseFormReturn<DatosReclamanteFormData>["reset"];
}

function Step1Render({ methods, setValue }: Step1RenderProps) {
  const {
    register,
    formState: { errors },
  } = methods;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <StepField
        label="Nombre completo"
        required
        error={errors.nombre_completo?.message}
        fullWidth
      >
        <Input
          id="nombre_completo"
          placeholder="Ej: Juan Pérez García"
          {...register("nombre_completo")}
          aria-invalid={!!errors.nombre_completo}
        />
      </StepField>

      <StepField
        label="Domicilio"
        required
        error={errors.domicilio?.message}
        fullWidth
      >
        <Input
          id="domicilio"
          placeholder="Ej: Av. Arequipa 1234, Lima"
          {...register("domicilio")}
          aria-invalid={!!errors.domicilio}
        />
      </StepField>

      <StepField
        label="Tipo de documento"
        required
        error={errors.tipo_documento?.message}
      >
        <Select
          onValueChange={(val) =>
            setValue("tipo_documento", val as "DNI" | "CE", {
              shouldValidate: true,
            })
          }
          defaultValue={DATOS_RECLAMANTE_DEFAULTS.tipo_documento}
        >
          <SelectTrigger
            id="tipo_documento"
            aria-invalid={!!errors.tipo_documento}
          >
            <SelectValue placeholder="Seleccione..." />
          </SelectTrigger>
          <SelectContent>
            {TIPO_DOCUMENTO_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </StepField>

      <StepField
        label="Número de documento"
        required
        error={errors.numero_documento?.message}
      >
        <Input
          id="numero_documento"
          placeholder="Ej: 12345678"
          {...register("numero_documento")}
          aria-invalid={!!errors.numero_documento}
        />
      </StepField>

      <StepField label="Teléfono" error={errors.telefono?.message}>
        <Input
          id="telefono"
          type="tel"
          placeholder="Ej: 999 888 777"
          {...register("telefono")}
          aria-invalid={!!errors.telefono}
        />
      </StepField>

      <StepField label="E-mail" error={errors.email?.message}>
        <Input
          id="email"
          type="email"
          placeholder="correo@ejemplo.com"
          {...register("email")}
          aria-invalid={!!errors.email}
        />
      </StepField>
    </div>
  );
}

// ── Step 2: Bien Reclamado ────────────────────────────────────────────────────

interface Step2RenderProps {
  methods: UseFormReturn<BienReclamadoFormData>;
  aggregate: Record<string, unknown>;
  setValue: UseFormReturn<BienReclamadoFormData>["setValue"];
  reset: UseFormReturn<BienReclamadoFormData>["reset"];
}

function Step2Render({ methods, setValue }: Step2RenderProps) {
  const {
    register,
    formState: { errors },
  } = methods;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <StepField
        label="Tipo de bien"
        required
        error={errors.tipo_bien?.message}
      >
        <Select
          onValueChange={(val) =>
            setValue("tipo_bien", val as "PRODUCTO" | "SERVICIO", {
              shouldValidate: true,
            })
          }
          defaultValue={BIEN_RECLAMADO_DEFAULTS.tipo_bien}
        >
          <SelectTrigger id="tipo_bien" aria-invalid={!!errors.tipo_bien}>
            <SelectValue placeholder="Seleccione..." />
          </SelectTrigger>
          <SelectContent>
            {TIPO_BIEN_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </StepField>

      <StepField
        label="Descripción del bien / servicio"
        required
        error={errors.descripcion_bien?.message}
        fullWidth
      >
        <Input
          id="descripcion_bien"
          placeholder="Ej: Servicio de consultoría técnica"
          {...register("descripcion_bien")}
          aria-invalid={!!errors.descripcion_bien}
        />
      </StepField>
    </div>
  );
}

// ── Step 3: Detalle de la Reclamación ────────────────────────────────────────

interface Step3RenderProps {
  methods: UseFormReturn<DetalleReclamacionFormData>;
  aggregate: Record<string, unknown>;
  setValue: UseFormReturn<DetalleReclamacionFormData>["setValue"];
  reset: UseFormReturn<DetalleReclamacionFormData>["reset"];
}

function Step3Render({ methods, setValue }: Step3RenderProps) {
  const {
    register,
    watch,
    formState: { errors },
  } = methods;

  const tipoReclamacion = watch("tipo_reclamacion");

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Tipo de reclamación — full width */}
      <div className="md:col-span-2 space-y-2">
        <StepField
          label="Tipo de reclamación"
          required
          error={errors.tipo_reclamacion?.message}
        >
          <RadioGroup
            className="flex gap-6"
            defaultValue={DETALLE_RECLAMACION_DEFAULTS.tipo_reclamacion}
            onValueChange={(val) =>
              setValue("tipo_reclamacion", val as "RECLAMO" | "QUEJA", {
                shouldValidate: true,
              })
            }
          >
            {TIPO_RECLAMACION_OPTIONS.map((opt) => (
              <div key={opt.value} className="flex items-center gap-2">
                <RadioGroupItem value={opt.value} id={`tipo_${opt.value}`} />
                <Label
                  htmlFor={`tipo_${opt.value}`}
                  className="font-normal cursor-pointer"
                >
                  {opt.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </StepField>

        {/* Help text */}
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground space-y-1">
          <p className="flex items-start gap-1.5">
            <AlertTriangle className="h-3 w-3 mt-0.5 text-primary shrink-0" />
            <span>
              <strong>Reclamo:</strong> Disconformidad relacionada a productos o
              servicios.
            </span>
          </p>
          <p className="flex items-start gap-1.5">
            <AlertTriangle className="h-3 w-3 mt-0.5 text-primary shrink-0" />
            <span>
              <strong>Queja:</strong> Disconformidad no relacionada a
              productos/servicios o malestar por la atención recibida.
            </span>
          </p>
        </div>
      </div>

      <StepField
        label="Área u oficina"
        required
        error={errors.area_oficina?.message}
        fullWidth
      >
        <Input
          id="area_oficina"
          placeholder="Ej: Área de Atención al Cliente"
          {...register("area_oficina")}
          aria-invalid={!!errors.area_oficina}
        />
      </StepField>

      <StepField
        label="Descripción / detalle"
        required
        error={errors.descripcion_detalle?.message}
        fullWidth
      >
        <Textarea
          id="descripcion_detalle"
          placeholder="Describa el motivo de su reclamación o queja..."
          rows={4}
          {...register("descripcion_detalle")}
          aria-invalid={!!errors.descripcion_detalle}
        />
      </StepField>

      {tipoReclamacion === "RECLAMO" && (
        <StepField
          label="Pedido del consumidor / acción solicitada"
          error={errors.pedido_accion?.message}
          fullWidth
        >
          <Textarea
            id="pedido_accion"
            placeholder="Indique la acción que solicita para resolver su reclamo..."
            rows={3}
            {...register("pedido_accion")}
            aria-invalid={!!errors.pedido_accion}
          />
        </StepField>
      )}
    </div>
  );
}

// ── Step 4: Confirmación ──────────────────────────────────────────────────────

interface Step4RenderProps {
  aggregate: Record<string, unknown>;
}

function Step4Render({ aggregate }: Step4RenderProps) {
  const datos = aggregate.datosReclamante as
    | DatosReclamanteFormData
    | undefined;
  const bien = aggregate.bienReclamado as BienReclamadoFormData | undefined;
  const detalle = aggregate.detalleReclamacion as
    | DetalleReclamacionFormData
    | undefined;

  const InfoRow = ({
    label,
    value,
  }: {
    label: string;
    value?: string | null;
  }) => (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
      <span className="text-sm font-semibold text-foreground">
        {value || (
          <span className="text-muted-foreground italic">No especificado</span>
        )}
      </span>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Resumen del reclamante */}
      <div className="rounded-xl border border-border/60 bg-card p-4 space-y-3">
        <div className="flex items-center gap-2 border-b border-border/40 pb-2">
          <User className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold uppercase tracking-wide">
            Datos del Reclamante
          </h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <InfoRow label="Nombre completo" value={datos?.nombre_completo} />
          <InfoRow label="Domicilio" value={datos?.domicilio} />
          <InfoRow
            label="Documento"
            value={
              datos
                ? `${datos.tipo_documento} – ${datos.numero_documento}`
                : undefined
            }
          />
          <InfoRow label="Teléfono" value={datos?.telefono ?? undefined} />
          <InfoRow
            label="Correo electrónico"
            value={datos?.email ?? undefined}
          />
        </div>
      </div>

      {/* Resumen del bien */}
      <div className="rounded-xl border border-border/60 bg-card p-4 space-y-3">
        <div className="flex items-center gap-2 border-b border-border/40 pb-2">
          <Building2 className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold uppercase tracking-wide">
            Bien Reclamado
          </h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <InfoRow
            label="Tipo"
            value={bien?.tipo_bien === "PRODUCTO" ? "Producto" : "Servicio"}
          />
          <InfoRow label="Descripción" value={bien?.descripcion_bien} />
        </div>
      </div>

      {/* Resumen del detalle */}
      <div className="rounded-xl border border-border/60 bg-card p-4 space-y-3">
        <div className="flex items-center gap-2 border-b border-border/40 pb-2">
          <FileText className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold uppercase tracking-wide">
            Detalle de la Reclamación
          </h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <InfoRow
            label="Tipo"
            value={
              detalle?.tipo_reclamacion === "RECLAMO" ? "Reclamo" : "Queja"
            }
          />
          <InfoRow label="Área / Oficina" value={detalle?.area_oficina} />
          <div className="sm:col-span-2">
            <InfoRow label="Descripción" value={detalle?.descripcion_detalle} />
          </div>
          {detalle?.pedido_accion && (
            <div className="sm:col-span-2">
              <InfoRow
                label="Acción solicitada"
                value={detalle.pedido_accion}
              />
            </div>
          )}
        </div>
      </div>

      {/* Legal notice */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-primary shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-xs font-semibold text-foreground">
            Declaración de buena fe
          </p>
          <p className="text-xs text-muted-foreground">
            Al enviar este formulario, declaro que la información proporcionada
            es verídica y conozco que la presentación de información falsa está
            sujeta a las sanciones establecidas en la legislación vigente.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Confirmation Success State ────────────────────────────────────────────────

interface ConfirmacionExitoProps {
  codigo: string;
  onNuevaReclamacion: () => void;
}

function ConfirmacionExito({
  codigo,
  onNuevaReclamacion,
}: ConfirmacionExitoProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-6 text-center px-4">
      <div className="p-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
        <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
      </div>
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-foreground">
          ¡Reclamación registrada!
        </h2>
        <p className="text-muted-foreground max-w-md text-sm">
          Su reclamación ha sido registrada exitosamente. Le recomendamos
          guardar el código de seguimiento para futuras consultas.
        </p>
      </div>

      {/* Constancia */}
      <div className="w-full max-w-sm rounded-xl border border-border/60 bg-card p-5 space-y-3">
        <div className="flex items-center gap-2 border-b border-border/40 pb-2">
          <ShieldCheck className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold uppercase tracking-wide">
            Constancia de registro
          </h3>
        </div>
        <div className="rounded-lg bg-muted/60 p-4 font-mono text-sm space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground text-xs">Código:</span>
            <span className="font-bold text-primary">{codigo}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground text-xs">Fecha:</span>
            <span className="text-xs">
              {new Date().toLocaleDateString("es-PE", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground text-xs">Estado:</span>
            <span className="text-xs font-semibold text-green-600 dark:text-green-400">
              Registrado
            </span>
          </div>
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <Button variant="outline" onClick={onNuevaReclamacion}>
          Nueva reclamación
        </Button>
      </div>
    </div>
  );
}

// ── Main exported component ───────────────────────────────────────────────────

export function LibroReclamacionesForm() {
  const { isOpen, isSubmitted, isSubmitting, close, reset } =
    useLibroReclamacionesUIStore();

  const _formId = useId();

  const handleSubmit = async (_data: unknown) => {
    // Simulate network latency — mock only, no backend
    await new Promise((resolve) => setTimeout(resolve, 800));
    notify.success("Reclamación registrada correctamente");
    close();
  };

  const handleClose = useCallback(
    (nextOpen: boolean) => {
      if (!nextOpen) {
        close();
      }
    },
    [close],
  );

  // Parts configuration for MultiPartFormStepper
  // biome-ignore lint/suspicious/noExplicitAny: Parts have per-step schemas; array typing requires any here.
  const parts: PartFormConfig<any>[] = useMemo(
    () => [
      {
        id: "datosReclamante",
        title: "Datos del Reclamante",
        description: "Identificación del consumidor reclamante",
        icon: User,
        schema: DatosReclamanteSchema,
        defaultValues: DATOS_RECLAMANTE_DEFAULTS,
        toAggregate: (
          data: DatosReclamanteFormData,
          agg: Record<string, unknown>,
        ) => ({ ...agg, datosReclamante: data }),
        render: (ctx: {
          methods: UseFormReturn<DatosReclamanteFormData>;
          aggregate: Record<string, unknown>;
          setValue: UseFormReturn<DatosReclamanteFormData>["setValue"];
          reset: UseFormReturn<DatosReclamanteFormData>["reset"];
        }) => <Step1Render {...ctx} />,
      },
      {
        id: "bienReclamado",
        title: "Bien Reclamado",
        description: "Identificación del bien contratado",
        icon: Building2,
        schema: BienReclamadoSchema,
        defaultValues: BIEN_RECLAMADO_DEFAULTS,
        toAggregate: (
          data: BienReclamadoFormData,
          agg: Record<string, unknown>,
        ) => ({ ...agg, bienReclamado: data }),
        render: (ctx: {
          methods: UseFormReturn<BienReclamadoFormData>;
          aggregate: Record<string, unknown>;
          setValue: UseFormReturn<BienReclamadoFormData>["setValue"];
          reset: UseFormReturn<BienReclamadoFormData>["reset"];
        }) => <Step2Render {...ctx} />,
      },
      {
        id: "detalleReclamacion",
        title: "Detalle",
        description: "Detalle de la reclamación",
        icon: ClipboardList,
        schema: DetalleReclamacionSchema,
        defaultValues: DETALLE_RECLAMACION_DEFAULTS,
        toAggregate: (
          data: DetalleReclamacionFormData,
          agg: Record<string, unknown>,
        ) => ({ ...agg, detalleReclamacion: data }),
        render: (ctx: {
          methods: UseFormReturn<DetalleReclamacionFormData>;
          aggregate: Record<string, unknown>;
          setValue: UseFormReturn<DetalleReclamacionFormData>["setValue"];
          reset: UseFormReturn<DetalleReclamacionFormData>["reset"];
        }) => <Step3Render {...ctx} />,
      },
      {
        id: "confirmar",
        title: "Confirmar",
        description: "Revise y envíe su reclamación",
        icon: ShieldCheck,
        schema: z.object({}), // Confirmation step — no extra validation needed
        defaultValues: {},
        toAggregate: (data: unknown, agg: Record<string, unknown>) => ({
          ...agg,
          confirmar: data,
        }),
        render: (ctx: { aggregate: Record<string, unknown> }) => (
          <Step4Render aggregate={ctx.aggregate} />
        ),
      },
    ],
    [],
  );

  return (
    <>
      {/* Trigger button — rendered by parent (page.tsx) */}
      {/* Inline success state — shown in-page when submitted */}
      {isSubmitted && (
        <ConfirmacionExito
          codigo={`LR-${Date.now().toString(36).toUpperCase()}`}
          onNuevaReclamacion={reset}
        />
      )}

      {/* Stepper modal */}
      <MultiPartFormStepper
        open={isOpen}
        onOpenChange={handleClose}
        title="Libro de Reclamaciones"
        eyebrow="Trámite documentario"
        icon={<BookOpen className="h-5 w-5 text-primary" />}
        description="Formulario de reclamaciones y quejas — Ley N° 29571"
        parts={parts}
        mapToFinal={(agg) => {
          const dr = agg.datosReclamante as DatosReclamanteFormData;
          const br = agg.bienReclamado as BienReclamadoFormData;
          const dt = agg.detalleReclamacion as DetalleReclamacionFormData;
          return {
            nombre_completo: dr?.nombre_completo,
            domicilio: dr?.domicilio,
            tipo_documento: dr?.tipo_documento,
            numero_documento: dr?.numero_documento,
            telefono: dr?.telefono,
            email: dr?.email,
            tipo_bien: br?.tipo_bien,
            descripcion_bien: br?.descripcion_bien,
            tipo_reclamacion: dt?.tipo_reclamacion,
            area_oficina: dt?.area_oficina,
            descripcion_detalle: dt?.descripcion_detalle,
            pedido_accion: dt?.pedido_accion,
          };
        }}
        onSubmit={handleSubmit}
        isLoading={isSubmitting}
        primaryLabel="Enviar reclamación"
        primaryLoadingLabel="Registrando..."
        cancelLabel="Cancelar"
        backLabel="Anterior"
        nextLabel="Siguiente"
        preventClose={isSubmitting}
        size="lg"
      />
    </>
  );
}
