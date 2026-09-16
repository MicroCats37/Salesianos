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
/**
 * ExpedienteFormModal — formulario de creación de expediente en modal custom.
 *
 * Sigue el mismo patrón que SolicitudFormModal:
 * - GenericModal + GenericForm directo (sin AppFormModal ni AppStepperFormModal).
 * - Stepper manual de 3 pasos con estado currentStep local.
 * - Smart Fields del registry (GenericForm + formSections + customFields).
 * - Todos los campos siempre visibles (sin field.hidden dinámico por tipo_persona).
 * - Validación por Zod via zodResolver en el schema del form.
 */
import { useCallback, useId, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type {
  FormField,
  SectionWrapperProps,
} from "@/components/genericForm/GenericInput";
import { InputFileCollection } from "@/components/genericForm/inputs/InputFileCollection";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FormSectionHeader } from "@/components-app/forms/FormSectionHeader";
import { notify } from "@/errors";
import { ExpedientePrintPreview } from "@/features/tramites/components/ExpedientePrintPreview";
import { PrintPreviewModal } from "@/features/tramites/components/PrintPreviewModal";
import { buildExpedientePrintHTML } from "@/features/tramites/components/printExpediente";
import { useCrearExpediente } from "@/features/tramites/hooks/useTramites";
import type { ExpedienteDetail } from "@/features/tramites/schemas/tramite.schema";
import { cn } from "@/lib/utils";

interface ExpedienteFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

// ── Enums y regex (alineados con crearSolicitud.schema) ────────────────────────

const TIPO_PERSONA = ["NATURAL", "JURIDICA", "COLEGIADO"] as const;

const DNI_REGEX = /^\d{8}$/;
const RUC_REGEX = /^\d{11}$/;
const CIP_REGEX = /^\d{1,6}$/;
const TELEFONO_REGEX = /^\+?\d{6,12}$/;

const TIPO_ARCHIVO_ENUM = ["PRINCIPAL", "ANEXO"] as const;

// ── Schema del form (estructura plana con array de archivos) ─────────────────

/**
 * Schema del form de Expediente (plano, con archivos como array).
 * El InputFileCollection produce este shape; el handleSubmit agrupa
 * por tipo al enviar al backend (que espera { principal: [], anexo: [] }).
 */
const ArchivoFormItemSchema = z.object({
  tipo_archivo: z.enum(TIPO_ARCHIVO_ENUM),
  nombre_original: z.string(),
  descripcion: z.string().nullable().optional(),
  file: z.instanceof(File),
});

const ExpedienteFormSchema = z.object({
  tipo_persona: z.enum(TIPO_PERSONA, {
    message: "Selecciona un tipo de persona",
  }),

  dni: z
    .string()
    .regex(DNI_REGEX, { message: "El DNI debe tener exactamente 8 dígitos" })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  ruc: z
    .string()
    .regex(RUC_REGEX, { message: "El RUC debe tener exactamente 11 dígitos" })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  cip: z
    .string()
    .regex(CIP_REGEX, { message: "El CIP debe tener hasta 6 dígitos" })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  razon_social: z.string().max(255).nullable().optional(),
  nombres: z.string().max(150).nullable().optional(),
  apellidos: z.string().max(150).nullable().optional(),
  correo: z
    .string()
    .email("Ingresa un correo electrónico válido")
    .max(255)
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),
  telefono: z
    .string()
    .regex(TELEFONO_REGEX, {
      message: "El teléfono debe tener entre 6 y 12 dígitos",
    })
    .max(12)
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  tipo_documento_id: z
    .string()
    .uuid({ message: "Selecciona un tipo de documento" })
    .nullable()
    .optional(),
  numero_documento: z.string().max(50).nullable().optional(),
  numero_folios: z
    .number({ message: "Los folios deben ser un número" })
    .int("Los folios deben ser un número entero")
    .min(0, "Los folios no pueden ser negativos")
    .default(0),

  asunto: z
    .string()
    .min(1, "El asunto es requerido")
    .max(500, "El asunto no puede exceder 500 caracteres"),

  observaciones: z.string().max(1000).nullable().optional(),

  // Array plano de archivos (PRINCIPAL/ANEXO) — se agrupa en handleSubmit
  archivos: z.array(ArchivoFormItemSchema).default([]),
});

type ExpedienteFormData = z.infer<typeof ExpedienteFormSchema>;

const EXPEDIENTE_FORM_DEFAULT: Partial<ExpedienteFormData> = {
  tipo_persona: "NATURAL",
  numero_folios: 0,
  archivos: [],
  dni: null,
  ruc: null,
  cip: null,
  razon_social: null,
  nombres: null,
  apellidos: null,
  correo: null,
  telefono: null,
  tipo_documento_id: null,
  numero_documento: null,
  asunto: "",
  observaciones: null,
};

// ── Options para Smart Fields ─────────────────────────────────────────────────

const TIPO_PERSONA_OPTIONS = [
  { label: "Persona Natural", value: "NATURAL" },
  { label: "Persona Jurídica", value: "JURIDICA" },
  { label: "Colegiado", value: "COLEGIADO" },
] as const;

// ── Field names para los Smart Fields de documento ───────────────────────────

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

// ── Step definitions ─────────────────────────────────────────────────────────

const STEPS = [
  { id: "datos", title: "Datos", icon: FileText },
  { id: "archivos", title: "Archivos", icon: Paperclip },
  { id: "revision", title: "Revisión", icon: Send },
] as const;

const TOTAL_STEPS = STEPS.length;

// ── Card wrapper (patrón liquidaciones) ─────────────────────────────────────

const SectionCard: React.FC<SectionWrapperProps> = ({
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

// ── Form Fields por sección ──────────────────────────────────────────────────

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
    placeholder: "Describa el motivo del expediente...",
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

// ── Componente principal ─────────────────────────────────────────────────────

export function ExpedienteFormModal({
  open,
  onOpenChange,
  onSuccess,
}: ExpedienteFormModalProps) {
  const formId = useId();
  const crearExpediente = useCrearExpediente();

  // Único useForm compartido por todos los pasos del stepper.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formMethods = useForm<ExpedienteFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(ExpedienteFormSchema) as any,
    defaultValues: EXPEDIENTE_FORM_DEFAULT,
    mode: "onBlur",
  });

  const [currentStep, setCurrentStep] = useState(0);
  const [printOpen, setPrintOpen] = useState(false);
  const [printItem, setPrintItem] = useState<ExpedienteDetail | null>(null);
  const [printHtml, setPrintHtml] = useState("");
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOTAL_STEPS - 1;

  const handleClose = (nextOpen: boolean) => {
    if (!nextOpen) {
      formMethods.reset(EXPEDIENTE_FORM_DEFAULT);
      setCurrentStep(0);
    }
    onOpenChange(nextOpen);
  };

  // Validación por paso antes de avanzar.
  const handleNext = useCallback(async () => {
    const fieldsToValidate: (keyof ExpedienteFormData)[] =
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
          ? ["archivos"]
          : [];

    const ok = await formMethods.trigger(fieldsToValidate as never);
    if (!ok) return;
    if (!isLastStep) setCurrentStep((s) => s + 1);
  }, [currentStep, formMethods, isLastStep]);

  const handleBack = useCallback(() => {
    if (!isFirstStep) setCurrentStep((s) => s - 1);
  }, [isFirstStep]);

  // Submit: agrupa archivos por tipo y arma el payload nested que espera el backend.
  const handleSubmit = useCallback(
    async (data: ExpedienteFormData) => {
      try {
        const archivosAgrupados = {
          principal: (data.archivos ?? [])
            .filter((a) => a.tipo_archivo === "PRINCIPAL")
            .map((a) => ({
              tipo_archivo: a.tipo_archivo,
              nombre_original: a.nombre_original,
              descripcion: a.descripcion ?? null,
              archivo: a.file,
            })),
          anexo: (data.archivos ?? [])
            .filter((a) => a.tipo_archivo === "ANEXO")
            .map((a) => ({
              tipo_archivo: a.tipo_archivo,
              nombre_original: a.nombre_original,
              descripcion: a.descripcion ?? null,
              archivo: a.file,
            })),
        };

        const payload = {
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
        };

        // mutateAsync retorna el envelope crudo de la API (no desenvuelto).
        // El onSuccess del useGenericCreateMutation desenvuelve para el prepend,
        // pero el await nos da el envelope. Extraemos data.
        const envelope = (await crearExpediente.mutateAsync(
          payload as never,
        )) as unknown as { data?: ExpedienteDetail } | undefined;
        const creado =
          envelope?.data ??
          (envelope as unknown as ExpedienteDetail | undefined);

        notify.success("Expediente creado correctamente");
        formMethods.reset(EXPEDIENTE_FORM_DEFAULT);
        setCurrentStep(0);
        onSuccess?.();

        // Abrir el preview de impresión con el expediente recién creado.
        if (creado && creado.id) {
          setPrintItem(creado);
          setPrintHtml(buildExpedientePrintHTML(creado as never));
          setPrintOpen(true);
        }
      } catch {
        // Error toast ya lo maneja useGenericCreateMutation.
      }
    },
    [crearExpediente, formMethods, onSuccess],
  );

  return (
    <>
      <GenericModal
        open={open}
        onOpenChange={handleClose}
        preventClose={crearExpediente.isPending}
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
                  Nuevo Expediente
                </h2>
                <p className="hidden sm:block max-w-prose text-pretty line-clamp-2 text-sm text-muted-foreground leading-relaxed">
                  Complete los datos del expediente y adjunte los archivos.
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
              <GenericForm<ExpedienteFormData>
                formId={`${formId}-step-0`}
                formMethods={formMethods}
                formSections={
                  STEP_1_SECTIONS as Parameters<
                    typeof GenericForm
                  >[0]["formSections"]
                }
                schema={ExpedienteFormSchema}
                initialData={EXPEDIENTE_FORM_DEFAULT}
                onSubmit={async () => {
                  /* submit real solo en el último paso */
                }}
                skipFooter
              />
            )}

            {currentStep === 1 && (
              <GenericForm<ExpedienteFormData>
                formId={`${formId}-step-1`}
                formMethods={formMethods}
                fields={[
                  {
                    name: "archivos",
                    label: "Archivos Adjuntos",
                    type: "custom",
                    containerClassName: "md:col-span-12",
                  },
                ]}
                schema={ExpedienteFormSchema}
                initialData={EXPEDIENTE_FORM_DEFAULT}
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

            {currentStep === 2 && (
              <GenericForm<ExpedienteFormData>
                formId={`${formId}-step-2`}
                formMethods={formMethods}
                fields={[]}
                schema={ExpedienteFormSchema}
                initialData={EXPEDIENTE_FORM_DEFAULT}
                onSubmit={handleSubmit}
                isLoading={crearExpediente.isPending}
                skipFooter
              >
                {() => <RevisionStep formMethods={formMethods} />}
              </GenericForm>
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
                  disabled={crearExpediente.isPending}
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
                    disabled={crearExpediente.isPending}
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
                    disabled={crearExpediente.isPending}
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
                    disabled={crearExpediente.isPending}
                    className="gap-2 font-bold"
                  >
                    {crearExpediente.isPending ? (
                      "Creando..."
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Crear Expediente
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

      {/* ── Modal de impresión: se abre automáticamente al crear el expediente ── */}
      {printItem && (
        <PrintPreviewModal
          open={printOpen}
          onOpenChange={setPrintOpen}
          title={`Expediente ${printItem.id_publico}`}
          htmlContent={printHtml}
          previewContent={
            <ExpedientePrintPreview
              item={
                // El PrintPreviewModal espera ExpedienteItem; el detail
                // comparte los campos base. Usamos un cast seguro.
                printItem as never as Parameters<
                  typeof ExpedientePrintPreview
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

// ── Step de revisión (children render) ────────────────────────────────────────

interface RevisionStepProps {
  formMethods: import("react-hook-form").UseFormReturn<ExpedienteFormData>;
}

function RevisionStep({ formMethods }: RevisionStepProps) {
  const { watch } = formMethods;
  const data = watch();

  return (
    <div className="space-y-4">
      <FormSectionHeader
        title="Revisión Final"
        variant="soft"
        icon={CheckCircle2}
        description="Verifique los datos antes de crear el expediente."
      />

      <div className="rounded-xl border border-border/50 bg-card p-4 space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          <span className="text-muted-foreground font-medium">
            Tipo de Persona:
          </span>
          <span>{data.tipo_persona ?? "—"}</span>

          <span className="text-muted-foreground font-medium">
            {data.tipo_persona === "NATURAL"
              ? "DNI:"
              : data.tipo_persona === "JURIDICA"
                ? "RUC:"
                : "CIP:"}
          </span>
          <span className="font-mono">
            {data.dni ?? data.ruc ?? data.cip ?? "—"}
          </span>

          <span className="text-muted-foreground font-medium">
            Nombres/Razón:
          </span>
          <span>
            {data.nombres
              ? `${data.nombres} ${data.apellidos ?? ""}`
              : (data.razon_social ?? "—")}
          </span>

          <span className="text-muted-foreground font-medium">Correo:</span>
          <span>{data.correo ?? "—"}</span>

          <span className="text-muted-foreground font-medium">Teléfono:</span>
          <span>{data.telefono ?? "—"}</span>

          <span className="text-muted-foreground font-medium">
            Tipo de Documento:
          </span>
          <span>{data.tipo_documento_id ? "(ID configurado)" : "—"}</span>

          <span className="text-muted-foreground font-medium">
            Número de Documento:
          </span>
          <span className="font-mono">{data.numero_documento ?? "—"}</span>

          <span className="text-muted-foreground font-medium">Folios:</span>
          <span>{data.numero_folios ?? 0}</span>

          <span className="text-muted-foreground font-medium">Asunto:</span>
          <span className="font-medium">{data.asunto ?? "—"}</span>

          <span className="text-muted-foreground font-medium">Archivos:</span>
          <span>
            {
              (data.archivos ?? []).filter(
                (a) => a.tipo_archivo === "PRINCIPAL",
              ).length
            }{" "}
            principal ·{" "}
            {
              (data.archivos ?? []).filter((a) => a.tipo_archivo === "ANEXO")
                .length
            }{" "}
            anexos
          </span>
        </div>

        {data.observaciones && (
          <div>
            <span className="text-muted-foreground font-medium block mb-1">
              Observaciones:
            </span>
            <p className="text-muted-foreground italic">{data.observaciones}</p>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-muted-foreground">
        <p>
          Al hacer clic en <strong>&quot;Crear Expediente&quot;</strong>, se
          validarán los datos y se creará el expediente con sus archivos
          adjuntos.
        </p>
      </div>
    </div>
  );
}
