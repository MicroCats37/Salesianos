"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  FilePlus,
  FileText,
  Mail,
  Paperclip,
  Phone,
  Send,
} from "lucide-react";
import type { FC } from "react";
/**
 * SolicitudFormModal — formulario de creación de solicitud en modal custom.
 *
 * UI: GenericModal + GenericForm directo (sin AppFormModal, sin AppStepperFormModal).
 * Stepper manual de 4 pasos (estado currentStep local) construido sobre GenericForm + Smart Fields.
 *
 * Sigue el patrón Smart Field (SMART_FIELD_ARCHITECTURE.md):
 * - Los inputs se renderizan automáticamente desde el registry pasando fields: FormField[].
 * - Las validaciones de Zod viven en el schema — el GenericForm las aplica vía zodResolver.
 * - Todos los campos son siempre visibles (sin field.hidden dinámico por tipo_persona).
 */
import { useCallback, useId, useState } from "react";
import { useForm } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type {
  FormField,
  SectionWrapperProps,
} from "@/components/genericForm/GenericInput";
import { InputAreaDistribution } from "@/components/genericForm/inputs/InputAreaDistribution";
import { InputFileCollection } from "@/components/genericForm/inputs/InputFileCollection";
import { InputSelect } from "@/components/genericForm/inputs/InputSelect";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FormSectionHeader } from "@/components-app/forms/FormSectionHeader";
import { notify } from "@/errors";

import { PrintPreviewModal } from "@/features/tramites/components/PrintPreviewModal";
import { buildSolicitudPrintHTML } from "@/features/tramites/components/printExpediente";
import { SolicitudPrintPreview } from "@/features/tramites/components/SolicitudPrintPreview";
import { useCrearTramite } from "@/features/tramites/hooks/useTramites";

import {
  CREAR_SOLICITUD_DEFAULT,
  type CrearSolicitudData,
  CrearSolicitudSchema,
} from "@/features/tramites/schemas/crearSolicitud.schema";
import type { SolicitudDetail } from "@/features/tramites/schemas/tramite.schema";
import { cn } from "@/lib/utils";

interface SolicitudFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

// ── Options para Smart Fields ─────────────────────────────────────────────────

const TIPO_PERSONA_OPTIONS = [
  { label: "Persona Natural", value: "NATURAL" },
  { label: "Persona Jurídica", value: "JURIDICA" },
  { label: "Colegiado", value: "COLEGIADO" },
] as const;

const PRIORIDAD_OPTIONS = [
  { label: "Baja", value: "BAJA" },
  { label: "Media", value: "MEDIA" },
  { label: "Alta", value: "ALTA" },
  { label: "Urgente", value: "URGENTE" },
] as const;

// ── Step definitions ─────────────────────────────────────────────────────────

const STEPS = [
  { id: "datos", title: "Datos", icon: FileText },
  { id: "areas", title: "Áreas", icon: Building2 },
  { id: "archivos", title: "Archivos", icon: Paperclip },
  { id: "revision", title: "Revisión", icon: Send },
] as const;

const TOTAL_STEPS = STEPS.length;

// ── Componente principal ─────────────────────────────────────────────────────

export function SolicitudFormModal({
  open,
  onOpenChange,
  onSuccess,
}: SolicitudFormModalProps) {
  const formId = useId();
  const crearTramite = useCrearTramite();

  // Único useForm compartido por todos los pasos del stepper.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formMethods = useForm<CrearSolicitudData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(CrearSolicitudSchema) as any,
    defaultValues: CREAR_SOLICITUD_DEFAULT,
    mode: "onBlur",
  });

  // ── Stepper state ──
  const [currentStep, setCurrentStep] = useState(0);
  const [printOpen, setPrintOpen] = useState(false);
  const [printItem, setPrintItem] = useState<SolicitudDetail | null>(null);
  const [printHtml, setPrintHtml] = useState("");
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOTAL_STEPS - 1;

  const handleClose = (nextOpen: boolean) => {
    if (!nextOpen) {
      formMethods.reset(CREAR_SOLICITUD_DEFAULT);
      setCurrentStep(0);
    }
    onOpenChange(nextOpen);
  };

  // ── Stepper navigation con validación por paso ──
  const handleNext = useCallback(async () => {
    // Validar solo los campos del paso actual antes de avanzar
    const fieldsToValidate: (keyof CrearSolicitudData)[] =
      currentStep === 0
        ? [
            "tipo_persona",
            "cip",
            "correo",
            "telefono",
            "tipo_documento_id",
            "numero_documento",
            "numero_folios",
            "asunto",
            "observaciones",
          ]
        : currentStep === 1
          ? ["areas_distribucion"]
          : currentStep === 2
            ? ["archivos"]
            : ["prioridad"];

    const ok = await formMethods.trigger(fieldsToValidate as never);
    if (!ok) return;
    if (!isLastStep) setCurrentStep((s) => s + 1);
  }, [currentStep, formMethods, isLastStep]);

  const handleBack = useCallback(() => {
    if (!isFirstStep) setCurrentStep((s) => s - 1);
  }, [isFirstStep]);

  // ── Submit: transforma al payload anidado del backend ──
  const handleSubmit = useCallback(
    async (data: CrearSolicitudData) => {
      try {
        // Agrupar archivos por tipo_archivo para el backend
        // El componente guarda el File como `file`; aquí lo mapeamos a `archivo`
        // para que coincida con el shape que espera el backend.
        const archivosAgrupados = {
          principal: data.archivos
            .filter((a) => a.tipo_archivo === "PRINCIPAL")
            .map((a) => ({
              tipo_archivo: a.tipo_archivo,
              nombre_original: a.nombre_original,
              descripcion: a.descripcion ?? null,
              archivo: a.file,
            })),
          anexo: data.archivos
            .filter((a) => a.tipo_archivo === "ANEXO")
            .map((a) => ({
              tipo_archivo: a.tipo_archivo,
              nombre_original: a.nombre_original,
              descripcion: a.descripcion ?? null,
              archivo: a.file,
            })),
        };

        const payload = {
          prioridad: data.prioridad,
          observacion: data.observacion ?? null,
          areas_distribucion: data.areas_distribucion,
          antecedentes: [],
          expediente: {
            tipo_persona: data.tipo_persona,
            dni: data.dni ?? null,
            ruc: data.ruc ?? null,
            cip: data.cip ?? null,
            razon_social: data.razon_social ?? null,
            nombres: data.nombres ?? null,
            apellidos: data.apellidos ?? null,
            correo: data.correo ?? null,
            telefono: data.telefono ?? null,
            tipo_documento_id: data.tipo_documento_id,
            numero_documento: data.numero_documento ?? null,
            numero_folios: data.numero_folios ?? 0,
            asunto: data.asunto,
            observaciones: data.observaciones ?? null,
            archivos: archivosAgrupados,
          },
        };

        // mutateAsync retorna el envelope crudo de la API (no desenvuelto).
        // Extraemos data del envelope.
        const envelope = (await crearTramite.mutateAsync(
          payload as never,
        )) as unknown as { data?: SolicitudDetail } | undefined;
        const creado =
          envelope?.data ??
          (envelope as unknown as SolicitudDetail | undefined);

        notify.success("Solicitud creada correctamente");
        formMethods.reset(CREAR_SOLICITUD_DEFAULT);
        setCurrentStep(0);
        onSuccess?.();

        // Abrir el preview de impresión con la solicitud recién creada.
        if (creado && creado.id) {
          setPrintItem(creado);
          setPrintHtml(buildSolicitudPrintHTML(creado as never));
          setPrintOpen(true);
        }
      } catch {
        // Error toast ya lo maneja useGenericCreateMutation.
      }
    },
    [crearTramite, formMethods, onSuccess],
  );

  return (
    <>
      <GenericModal
        open={open}
        onOpenChange={handleClose}
        preventClose={crearTramite.isPending}
      >
        <GenericModal.Content size="xl">
          {/* ── Header custom ──────────────────────────────────────────── */}
          <div className="bg-gradient-to-r from-primary/5 via-primary/[0.02] to-transparent border-b border-border px-6 py-5 sm:px-8">
            <div className="flex items-center gap-3 w-full">
              <div className="p-2 sm:p-2.5 bg-primary/10 rounded-xl sm:rounded-2xl border border-primary/20 shadow-sm shrink-0">
                <FilePlus className="h-5 w-5 text-primary" />
              </div>
              <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                <span className="hidden sm:block text-[10px] font-bold uppercase tracking-widest text-primary leading-none">
                  Mesa de Partes
                </span>
                <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground leading-tight">
                  Nueva Solicitud
                </h2>
                <p className="hidden sm:block max-w-prose text-pretty line-clamp-2 text-sm text-muted-foreground leading-relaxed">
                  Complete los datos del expediente, asigne las áreas y adjunte
                  los archivos.
                </p>
              </div>
            </div>
          </div>

          {/* ── Stepper Header ─────────────────────────────────────────── */}
          <StepperProgress
            steps={
              STEPS as unknown as {
                id: string;
                title: string;
                icon: typeof FileText;
              }[]
            }
            currentStep={currentStep}
          />

          {/* ── Body: form por step ────────────────────────────────────── */}
          <GenericModal.Body>
            {currentStep === 0 && (
              <GenericForm<CrearSolicitudData>
                formId={`${formId}-step-0`}
                formMethods={formMethods}
                formSections={
                  STEP_1_SECTIONS as Parameters<
                    typeof GenericForm
                  >[0]["formSections"]
                }
                schema={CrearSolicitudSchema}
                initialData={CREAR_SOLICITUD_DEFAULT}
                onSubmit={async () => {
                  /* submit real solo en el último paso */
                }}
                skipFooter
              />
            )}

            {currentStep === 1 && (
              <GenericForm<CrearSolicitudData>
                formId={`${formId}-step-1`}
                formMethods={formMethods}
                fields={[
                  {
                    name: "areas_distribucion",
                    label: "Distribución de Áreas",
                    type: "custom",
                    containerClassName: "md:col-span-12",
                  },
                ]}
                schema={CrearSolicitudSchema}
                initialData={CREAR_SOLICITUD_DEFAULT}
                onSubmit={async () => {}}
                skipFooter
                customFields={{
                  areas_distribucion: () => (
                    <InputAreaDistribution
                      field={{
                        name: "areas_distribucion",
                        label: "Distribución de Áreas",
                        type: "area-distribution",
                      }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      control={formMethods.control as any}
                      id={`${formId}-area-distribution`}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      register={formMethods.register as any}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      error={
                        formMethods.formState.errors.areas_distribucion as any
                      }
                    />
                  ),
                }}
              />
            )}

            {currentStep === 2 && (
              <GenericForm<CrearSolicitudData>
                formId={`${formId}-step-2`}
                formMethods={formMethods}
                fields={[
                  {
                    name: "archivos",
                    label: "Archivos Adjuntos",
                    type: "custom",
                    containerClassName: "md:col-span-12",
                  },
                ]}
                schema={CrearSolicitudSchema}
                initialData={CREAR_SOLICITUD_DEFAULT}
                onSubmit={async () => {}}
                skipFooter
                customFields={{
                  archivos: () => (
                    <InputFileCollection
                      field={{
                        name: "archivos",
                        label: "Archivos Adjuntos",
                        type: "file-collection",
                      }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      control={formMethods.control as any}
                      id={`${formId}-file-collection`}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      register={formMethods.register as any}
                      fileKind="all"
                      maxFiles={20}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      error={formMethods.formState.errors.archivos as any}
                    />
                  ),
                }}
              />
            )}

            {currentStep === 3 && (
              <GenericForm<CrearSolicitudData>
                formId={`${formId}-step-3`}
                formMethods={formMethods}
                fields={STEP_4_FIELDS}
                schema={CrearSolicitudSchema}
                initialData={CREAR_SOLICITUD_DEFAULT}
                onSubmit={handleSubmit}
                isLoading={crearTramite.isPending}
                skipFooter
              />
            )}
          </GenericModal.Body>

          {/* ── Footer: navegación del stepper ─────────────────────────── */}
          <GenericModal.Footer className="px-6 py-4 sm:px-8 bg-muted/30 border-t border-border">
            <div className="flex items-center justify-between gap-2 sm:gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground hidden sm:inline">
                  Paso {currentStep + 1} de {TOTAL_STEPS}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleClose(false)}
                  disabled={crearTramite.isPending}
                  className="text-muted-foreground"
                >
                  Cancelar
                </Button>
              </div>

              <div className="flex items-center gap-2">
                {!isFirstStep && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleBack}
                    disabled={crearTramite.isPending}
                    className="gap-1"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span className="hidden sm:inline">Anterior</span>
                  </Button>
                )}

                {!isLastStep && (
                  <Button
                    type="button"
                    onClick={handleNext}
                    disabled={crearTramite.isPending}
                    className="gap-1"
                  >
                    <span>Siguiente</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                )}

                {isLastStep && (
                  <Button
                    type="button"
                    onClick={() => {
                      void formMethods.handleSubmit(handleSubmit as never)();
                    }}
                    disabled={crearTramite.isPending}
                    className="gap-2 font-bold"
                  >
                    {crearTramite.isPending ? (
                      "Creando..."
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Crear Solicitud
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </GenericModal.Footer>

          <GenericModal.CloseX />
        </GenericModal.Content>
      </GenericModal>

      {/* ── Modal de impresión: se abre automáticamente al crear la solicitud ── */}
      {printItem && (
        <PrintPreviewModal
          open={printOpen}
          onOpenChange={setPrintOpen}
          title={`Solicitud ${printItem.expediente?.id_publico ?? printItem.id}`}
          htmlContent={printHtml}
          previewContent={
            <SolicitudPrintPreview
              item={
                // El PrintPreviewModal espera SolicitudItem; el detail
                // comparte los campos base. Usamos un cast seguro.
                printItem as never as Parameters<
                  typeof SolicitudPrintPreview
                >[0]["item"]
              }
            />
          }
        />
      )}
    </>
  );
}

// ── Stepper progress ───────────────────────────────────────────────────────────

interface StepperProgressProps {
  steps: { id: string; title: string; icon: typeof FileText }[];
  currentStep: number;
}

function StepperProgress({ steps, currentStep }: StepperProgressProps) {
  return (
    <nav
      aria-label="Progreso del formulario"
      className="px-6 py-3 border-b border-border bg-muted/20"
    >
      <ol className="flex items-center gap-1">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStep;
          const isCurrent = idx === currentStep;
          const Icon = step.icon;
          return (
            <li key={step.id} className="flex items-center gap-1">
              <Badge
                variant="outline"
                className={cn(
                  "gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
                  isCurrent &&
                    "bg-primary text-primary-foreground border-primary shadow-sm",
                  isCompleted && "bg-primary/10 text-primary border-primary/30",
                  !isCurrent &&
                    !isCompleted &&
                    "bg-muted text-muted-foreground",
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{step.title}</span>
              </Badge>
              {idx < steps.length - 1 && (
                <div
                  className={cn(
                    "h-px w-4 sm:w-8 transition-colors",
                    idx < currentStep ? "bg-primary" : "bg-border",
                  )}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// ── Step 1 Sections: Datos del Solicitante, Contacto y Documento ────────────────
// Estructura organizada en cards con headers (patrón LiquidacionFormBodyBase).

/** Custom card wrapper: rounded-xl border bg-card con header visual. */
const SectionCard: FC<SectionWrapperProps> = ({
  children,
  title,
  icon: Icon,
}) => (
  <div className="rounded-xl border border-border/50 bg-card p-4 space-y-4">
    {title && (
      <div className="flex items-center gap-2 border-b border-border/40 pb-2">
        {Icon && <Icon className="h-4 w-4 text-primary" />}
        <h3 className="text-sm font-semibold uppercase tracking-wide">
          {title}
        </h3>
      </div>
    )}
    <div className="grid grid-cols-1 gap-4">{children}</div>
  </div>
);

// Field names para los Smart Fields de documento
// NOTA: el lookup NO escribe `tipo_documento` (ese es el tipo de documento del TRÁMITE,
// ej. OFICIO, CARTA, no el tipo de documento de identidad del solicitante).
const DNI_LOOKUP_FIELD_NAMES: Record<string, string> = {
  numero_documento: "dni",
  razon_social: "razon_social",
  nombres: "nombres",
  apellidos: "apellidos",
};

const RUC_LOOKUP_FIELD_NAMES: Record<string, string> = {
  numero_documento: "ruc",
  razon_social: "razon_social",
};

// ── Datos del Solicitante ─────────────────────────────────────────────────────
const SOLICITANTE_FIELDS: FormField[] = [
  {
    name: "tipo_persona",
    label: "Tipo de Persona",
    type: "select",
    options: TIPO_PERSONA_OPTIONS,
    required: true,
    containerClassName: "md:col-span-6",
  },
  {
    name: "dni",
    label: "DNI",
    type: "documento-lookup",
    fieldNames: DNI_LOOKUP_FIELD_NAMES,
    containerClassName: "md:col-span-12",
  },
  {
    name: "ruc",
    label: "RUC",
    type: "documento-lookup",
    fieldNames: RUC_LOOKUP_FIELD_NAMES,
    containerClassName: "md:col-span-12",
  },
  {
    name: "cip",
    label: "CIP",
    type: "text",
    placeholder: "Ej: 12345",
    containerClassName: "md:col-span-6",
  },
];

// ── Datos de Contacto ────────────────────────────────────────────────────────
const CONTACTO_FIELDS: FormField[] = [
  {
    name: "correo",
    label: "Correo",
    type: "text",
    placeholder: "correo@ejemplo.com",
    containerClassName: "md:col-span-6",
  },
  {
    name: "telefono",
    label: "Teléfono",
    type: "text",
    placeholder: "Ej: 999 888 777",
    containerClassName: "md:col-span-6",
  },
];

// ── Datos del Documento ───────────────────────────────────────────────────────
const DOCUMENTO_FIELDS: FormField[] = [
  {
    name: "tipo_documento_id",
    label: "Tipo de Documento",
    type: "select-tipo-documento",
    required: true,
    containerClassName: "md:col-span-6",
  },
  {
    name: "numero_documento",
    label: "Número de Documento",
    type: "text",
    placeholder: "Ej: 001-2024",
    containerClassName: "md:col-span-6",
  },
  {
    name: "numero_folios",
    label: "Número de Folios",
    type: "number",
    defaultValue: 0,
    min: 0,
    containerClassName: "md:col-span-6",
  },
  {
    name: "asunto",
    label: "Asunto",
    type: "textarea",
    placeholder: "Describa el motivo de su solicitud...",
    required: true,
    containerClassName: "md:col-span-12",
  },
  {
    name: "observaciones",
    label: "Observaciones",
    type: "textarea",
    placeholder: "Información adicional opcional...",
    containerClassName: "md:col-span-12",
  },
];

const STEP_1_SECTIONS = [
  {
    title: "Datos del Solicitante",
    icon: Building2,
    fields: SOLICITANTE_FIELDS,
    wrapper: SectionCard,
  },
  {
    title: "Datos de Contacto",
    icon: Phone,
    fields: CONTACTO_FIELDS,
    wrapper: SectionCard,
  },
  {
    title: "Datos del Documento",
    icon: FileText,
    fields: DOCUMENTO_FIELDS,
    wrapper: SectionCard,
  },
];

// ── Step 4 Fields: Prioridad y Observación ───────────────────────────────────

const STEP_4_FIELDS: FormField[] = [
  {
    name: "prioridad",
    label: "Prioridad",
    type: "select",
    options: PRIORIDAD_OPTIONS,
    defaultValue: "MEDIA",
    containerClassName: "md:col-span-6",
  },
  {
    name: "observacion",
    label: "Observación General",
    type: "textarea",
    placeholder: "Información adicional opcional...",
    containerClassName: "md:col-span-12",
  },
];
