"use client";

import { gsap } from "gsap";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  GraduationCap,
  Info,
  Loader2,
  Package,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Controller, useFormContext } from "react-hook-form";
import { toast } from "sonner";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { cn } from "@/lib/utils";
import { useCreateInscripcionCompleta } from "../hooks/useCreateInscripcionCompleta";
import { usePaquetes, usePromociones } from "../hooks/useInscripcionCatalogs";
import {
  type InscripcionFormData,
  InscripcionFormSchema,
} from "../schemas/inscripcion.schema";
import type { PaqueteListContract } from "../schemas/paquete.schema";
import { SmartEquipoField } from "./smart-fields/SmartEquipoField";
import { SmartPaqueteCardsField } from "./smart-fields/SmartPaqueteCardsField";
import { StepDeclarations } from "./steps/StepDeclarations";

// ── Step Config ───────────────────────────────────────────────────────────────

const STEPS = [
  { id: 1, label: "Paquete", icon: Package },
  { id: 2, label: "Equipos", icon: Users },
  { id: 3, label: "Declaraciones", icon: ShieldCheck },
];

// ── SmartSearchableSelectField ────────────────────────────────────────────────

interface SmartSearchableSelectFieldProps {
  name: "promocion_id" | "fusion_promocion_id";
  label: string;
  placeholder: string;
  options: { label: string; value: string }[];
  required?: boolean;
  disabled?: boolean;
}

function SmartSearchableSelectField({
  name,
  label,
  placeholder,
  options,
  required,
  disabled,
}: SmartSearchableSelectFieldProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext<InscripcionFormData>();
  const error = errors[name]?.message;

  return (
    <div className="space-y-1.5">
      <Label className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
        {label}
        {required && <span className="text-amber-600">*</span>}
      </Label>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <SearchableSelect
            id={name}
            label={label}
            value={(field.value as string | null) || null}
            onValueChange={field.onChange}
            options={options}
            placeholder={placeholder}
            icon={GraduationCap}
            disabled={disabled}
            error={!!error}
            errorMessage={error}
            showLabel={false}
            hideErrorMessage
            className="w-full [&_button]:w-full"
          />
        )}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

// ── Info Banner ──────────────────────────────────────────────────────────────

function InfoBanner({ step }: { step: number }) {
  const title =
    step === 1
      ? "Paso 1 · Paquete"
      : step === 2
        ? "Paso 2 · Equipos y promocion"
        : "Paso 3 · Declaraciones";

  const body =
    step === 1
      ? "Empieza eligiendo el paquete que mejor se adapta a tu equipo. Esto define cuantos equipos podras crear y cuantos participantes por equipo."
      : step === 2
        ? "Selecciona tu promocion (con fusion opcional) y luego crea un equipo por cada disciplina del paquete. Las personas se agregan despues desde el detalle de la inscripcion."
        : "Acepta las bases y declara el consentimiento. Recuerda: primero pagas la inscripcion del equipo y luego agregas a las personas.";

  return (
    <div
      className="flex items-start gap-4 rounded-2xl border border-sky-200 bg-gradient-to-r from-sky-50 via-indigo-50 to-amber-50 p-5 text-slate-700 shadow-md"
      role="note"
    >
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-indigo-600 shadow-md">
        <Info className="size-5 text-white" />
      </div>
      <div className="space-y-1">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-sky-700">
          {title}
        </p>
        <p className="text-sm leading-relaxed">{body}</p>
      </div>
    </div>
  );
}

// ── Main Wizard Component ──────────────────────────────────────────────────────

export function InscripcionWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const wizardRef = useRef<HTMLDivElement>(null);

  // Consents are LOCAL state — they are NOT in the form schema and NOT sent in
  // the backend payload. Backend records aceptaciones per-person via
  // POST /{inscripcion_id}/personas. The wizard validates them manually in
  // `onSubmit` and blocks the submit if any consent is missing.
  const [consents, setConsents] = useState({
    bases: false,
    aptitudFisica: false,
    imagen: false,
  });

  const createMutation = useCreateInscripcionCompleta();
  const promocionesQuery = usePromociones();
  const paquetesQuery = usePaquetes();
  const promocionOptions = (promocionesQuery.data ?? []).map((p) => ({
    value: p.id,
    label: `${p.nombre} · ${p.anio}`,
  }));

  const initialData: InscripcionFormData = {
    paquete_id: "",
    promocion_id: "",
    fusion_promocion_id: null,
    equipos: [],
    cantidad: undefined,
  };

  useEffect(() => {
    const wizard = wizardRef.current;
    if (!wizard) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".wizard-step",
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.1,
          ease: "power3.out",
        },
      );
    }, wizard);
    return () => ctx.revert();
  }, []);

  // Animate step transitions: fade/slide the active step container.
  useEffect(() => {
    if (!wizardRef.current) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const target = wizardRef.current.querySelector("[data-step-content]");
    if (!target) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        target,
        { x: 24, opacity: 0, filter: "blur(4px)" },
        {
          x: 0,
          opacity: 1,
          filter: "blur(0px)",
          duration: 0.5,
          ease: "power2.out",
        },
      );
    });
    return () => ctx.revert();
  }, [currentStep]);

  const onSubmit = async (data: InscripcionFormData) => {
    // Validate consents FIRST so the user is not surprised by a 422 from the
    // backend (the backend ignores consents in the atomic payload anyway).
    if (!consents.bases || !consents.aptitudFisica || !consents.imagen) {
      toast.error("Debes aceptar las 3 declaraciones para continuar");
      return;
    }
    // Derive the selected paquete from form state — never fetch post-selection.
    const selectedPaquete = (paquetesQuery.data ?? []).find(
      (p) => p.id === data.paquete_id,
    );
    if (!selectedPaquete) {
      toast.error("Selecciona un paquete antes de enviar");
      return;
    }
    // Use the cantidad set by the SmartPaqueteCardsField on selection.
    // Fall back to the package minimum if the user somehow didn't pick a card.
    const cantidad =
      data.cantidad ?? selectedPaquete.cantidad_minima_compra ?? 1;
    createMutation.mutate({
      evento_id: selectedPaquete.evento_id,
      paquete_id: selectedPaquete.id,
      promocion_id: data.promocion_id,
      fusion_promocion_id: data.fusion_promocion_id ?? null,
      delegado_id: null,
      cantidad,
      equipos: data.equipos.map((eq) => ({
        disciplina_id: eq.disciplina_id,
        categoria_id: eq.categoria_id ?? null,
        nombre: eq.nombre,
      })),
      observacion: "",
      // Propagar la cotización capturada en handleSelect. Si el usuario
      // seleccionó el card antes del debounce de 500ms, estos campos
      // quedan undefined y el backend usa el precio vigente del catálogo.
      precio_unitario_cotizado: data.precio_unitario_cotizado ?? null,
      cotizacion_version: data.cotizacion_version ?? null,
    });
  };

  const handlePrev = () => {
    setCurrentStep((s) => Math.max(s - 1, 1));
  };

  const stepFields: Record<number, ReadonlyArray<keyof InscripcionFormData>> = {
    1: ["paquete_id"],
    2: ["promocion_id", "equipos"],
    // Step 3 (Declarations) shows the submit button — consents live in local
    // state and are validated inside onSubmit before the form schema runs.
    3: [],
  };

  return (
    <div ref={wizardRef} className="w-full">
      <GenericForm<InscripcionFormData>
        schema={InscripcionFormSchema}
        initialData={initialData}
        onSubmit={onSubmit}
        formClassName="space-y-6"
        showErrorsAsToasts
      >
        {({ isSubmitting, methods }) => {
          return (
            <>
              {/* ── Branding Header ── */}
              <div className="flex flex-col items-center gap-2 pb-2">
                <FestBrandHeader
                  variant="onLight"
                  size="sm"
                  subtitle={`Preinscripcion · Paso ${currentStep} de ${STEPS.length}`}
                />
              </div>

              {/* ── Step Progress ── */}
              <div className="flex items-center justify-center gap-2 py-2">
                {STEPS.map((step) => {
                  const Icon = step.icon;
                  const isActive = currentStep === step.id;
                  const isCompleted = currentStep > step.id;
                  return (
                    <div key={step.id} className="flex items-center gap-2">
                      <div
                        className={cn(
                          "wizard-step flex h-9 w-9 items-center justify-center rounded-full border-2 text-xs font-bold transition-all shadow-sm",
                          isActive &&
                            "border-amber-500 bg-gradient-to-br from-amber-100 to-amber-50 text-amber-700 ring-2 ring-amber-200",
                          isCompleted &&
                            "border-emerald-500 bg-emerald-50 text-emerald-600",
                          !isActive &&
                            !isCompleted &&
                            "border-slate-200 bg-white text-slate-400",
                        )}
                      >
                        {isCompleted ? (
                          <Check className="size-4" />
                        ) : (
                          <Icon className="size-4" />
                        )}
                      </div>
                      <span
                        className={cn(
                          "hidden text-xs font-semibold sm:block",
                          isActive && "text-amber-700",
                          isCompleted && "text-emerald-600",
                          !isActive && !isCompleted && "text-slate-400",
                        )}
                      >
                        {step.label}
                      </span>
                      {step.id < STEPS.length && (
                        <div
                          className={cn(
                            "h-0.5 w-6 sm:w-10 rounded-full",
                            isCompleted ? "bg-emerald-500" : "bg-slate-200",
                          )}
                        />
                      )}
                    </div>
                  );
                })}
              </div>

              <InfoBanner step={currentStep} />

              {/* ── Step Content with desktop grid layout ── */}
              <div data-step-content className="wizard-step min-h-[360px]">
                {currentStep === 1 && (
                  <div className="space-y-6">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
                        <Package className="size-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-slate-900">
                          Selecciona tu paquete
                        </h3>
                        <p className="text-sm text-slate-500">
                          Escoge el paquete que mejor se adapte a tu equipo.
                        </p>
                      </div>
                    </div>
                    <SmartPaqueteCardsField fieldName="paquete_id" />
                  </div>
                )}

                {currentStep === 2 && (
                  <div className="space-y-6">
                    <div className="grid gap-4 lg:grid-cols-5">
                      <div className="lg:col-span-3">
                        <SmartSearchableSelectField
                          name="promocion_id"
                          label="Promocion"
                          placeholder="Busca tu promocion"
                          options={promocionOptions}
                          required
                          disabled={promocionesQuery.isLoading}
                        />
                      </div>
                      <div className="lg:col-span-2">
                        <SmartSearchableSelectField
                          name="fusion_promocion_id"
                          label="Fusion (opcional)"
                          placeholder="Solo si aplica"
                          options={promocionOptions}
                          disabled={promocionesQuery.isLoading}
                        />
                      </div>
                    </div>
                    <EquiposStepLayout
                      methods={methods}
                      paquetes={paquetesQuery.data}
                    />
                  </div>
                )}

                {currentStep === 3 && (
                  <StepDeclarations
                    consents={consents}
                    setConsents={setConsents}
                  />
                )}
              </div>

              {/* ── Navigation Buttons ── */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handlePrev}
                  disabled={currentStep === 1 || isSubmitting}
                  className="text-slate-600 hover:text-slate-900"
                >
                  <ArrowLeft className="size-4 mr-1" />
                  Anterior
                </Button>

                {currentStep < STEPS.length ? (
                  <Button
                    type="button"
                    onClick={async () => {
                      const fields = stepFields[currentStep] ?? [];
                      const valid =
                        fields.length === 0
                          ? true
                          : await methods.trigger(
                              fields as Parameters<typeof methods.trigger>[0],
                              { shouldFocus: true },
                            );
                      if (!valid) {
                        toast.error(
                          "Completa los campos obligatorios antes de continuar",
                        );
                        return;
                      }
                      setCurrentStep((s) => Math.min(s + 1, STEPS.length));
                    }}
                    className="bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-bold shadow-md hover:from-amber-600 hover:to-amber-700"
                  >
                    Siguiente
                    <ArrowRight className="size-4 ml-1" />
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold shadow-md hover:from-emerald-600 hover:to-emerald-700"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="size-4 mr-2 animate-spin" />
                        Enviando...
                      </>
                    ) : (
                      "Enviar inscripción"
                    )}
                  </Button>
                )}
              </div>
            </>
          );
        }}
      </GenericForm>
    </div>
  );
}

// ── Equipos Step Layout ──────────────────────────────────────────────────────

interface EquiposStepLayoutProps {
  methods: ReturnType<typeof useFormContext<InscripcionFormData>>;
  /**
   * Full `PaqueteListContract` list — El equipo field derives its
   * paqueteActual shape directly from this canonical list (no separate fetch).
   */
  paquetes: PaqueteListContract[] | undefined;
}

function EquiposStepLayout({ methods, paquetes }: EquiposStepLayoutProps) {
  const paqueteId = methods.watch("paquete_id");
  const paqueteActual = paquetes?.find((p) => p.id === paqueteId);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
          <Users className="size-5" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">Equipos</h3>
          <p className="text-sm text-slate-500">
            Crea un equipo por cada disciplina incluida en tu paquete. Las
            personas se agregan despues desde el detalle de la inscripcion.
          </p>
        </div>
      </div>

      <SmartEquipoField
        fieldName="equipos"
        paqueteIdFieldName="paquete_id"
        paqueteActual={
          paqueteActual
            ? {
                id: paqueteActual.id,
                cantidad_disciplinas: paqueteActual.cantidad_disciplinas,
                cantidad_minima_compra: paqueteActual.cantidad_minima_compra,
                cantidad_maxima_equipos: paqueteActual.cantidad_maxima_equipos,
                modo_disciplinas: paqueteActual.modo_disciplinas,
                disciplinas: paqueteActual.disciplinas,
              }
            : undefined
        }
      />
    </div>
  );
}
