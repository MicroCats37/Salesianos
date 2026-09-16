"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Sparkles,
  Trophy,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { notify } from "@/errors/toast-adapter";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { useCreateInscripcion } from "../hooks/useCreateInscripcion";
import { type InscripcionPayload, InscripcionPayloadSchema } from "../schemas";
import { Step1Responsable } from "./steps/Step1Responsable";
import { Step2Equipo } from "./steps/Step2Equipo";
import { Step3Paquete } from "./steps/Step3Paquete";
import { Step4Declaraciones } from "./steps/Step4Declaraciones";

const STEPS = [
  { num: 1, title: "Responsable", description: "Identifica al responsable" },
  { num: 2, title: "Equipo y nómina", description: "Arma la nómina deportiva" },
  {
    num: 3,
    title: "Paquete y pago",
    description: "Revisa el paquete Salesianos FEST",
  },
  {
    num: 4,
    title: "Declaraciones",
    description: "Acepta las condiciones de registro",
  },
];

export function InscripcionWizard() {
  const router = useRouter();
  const user = useAuthUser();
  const createMut = useCreateInscripcion();
  const [step, setStep] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // GenericForm (Mode 4 Hybrid) recibe este formMethods externo
  const form = useForm<InscripcionPayload>({
    resolver: zodResolver(InscripcionPayloadSchema),
    defaultValues: {
      userId: user?.id ?? "",
      promocionId: "",
      fusionPromocionId: null,
      basesId: "",
      paqueteMonto: 1350,
      teamName: "",
      acceptedBases: false,
      fitnessDeclaration: false,
      imageConsent: false,
      deportistas: [],
    },
    mode: "onChange",
  });

  // Cargar base activa + setear userId (después del mount, cuando el user existe)
  useEffect(() => {
    fetch("/api/catalogs/bases", { credentials: "include" })
      .then((res) => res.json())
      .then((json) => {
        if (json.success && json.data?.id) {
          form.setValue("basesId", json.data.id);
        }
      })
      .catch(() => {
        // Catalog fetch failure is non-fatal — form still works with empty basesId
      });
    if (user?.id) {
      form.setValue("userId", user.id);
    }
  }, [form, user]);

  // onSubmit del GenericForm — se dispara solo si Zod valida TODO el form
  const doSubmit = async (data: InscripcionPayload) => {
    await createMut.mutateAsync(data);
    notify.success("¡Inscripción enviada al Comité!");
    router.push("/dashboard");
  };

  const next = async () => {
    let valid = false;
    if (step === 0) valid = await form.trigger(["promocionId"]);
    if (step === 1) valid = await form.trigger(["teamName", "deportistas"]);
    if (step === 2) valid = true; // sin inputs, siempre válido
    if (step === 3)
      valid = await form.trigger([
        "fitnessDeclaration",
        "imageConsent",
        "acceptedBases",
      ]);
    if (valid) setStep(Math.min(step + 1, STEPS.length - 1));
  };

  // Evitar hydration mismatch: el usuario vive en localStorage (Zustand persist)
  if (!mounted) {
    return (
      <Card className="card-elevated w-full max-w-3xl mx-auto border-0 p-12 text-center shadow-2xl">
        <Loader2 className="mx-auto size-8 animate-spin text-[#312e8e]" />
        <p className="mt-4 text-sm text-muted-foreground">
          Cargando formulario...
        </p>
      </Card>
    );
  }

  return (
    <Card className="card-elevated w-full max-w-3xl mx-auto overflow-hidden border-0 shadow-2xl">
      {/* Header with brand gradient */}
      <div className="bg-gradient-to-br from-[#312e8e] to-[#25236f] px-6 py-6 text-white">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
            <Trophy className="size-6" />
          </div>
          <div>
            <CardTitle className="text-xl font-black text-white">
              Inscripción Salesianos FEST 2026
            </CardTitle>
            <p className="text-sm text-white/80">
              Paso {step + 1} de {STEPS.length} · {STEPS[step].title}
            </p>
          </div>
        </div>
      </div>

      {/* Stepper visual */}
      <div className="flex items-center justify-between border-b border-border bg-[#f4f6fb] px-6 py-4">
        {STEPS.map((s, idx) => {
          const isDone = idx < step;
          const isCurrent = idx === step;
          return (
            <div key={s.num} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-black transition ${
                    isDone
                      ? "bg-[#10b981] text-white shadow-lg shadow-[#10b981]/30"
                      : isCurrent
                        ? "bg-[#312e8e] text-white shadow-lg shadow-[#312e8e]/30 animate-pulse-slow"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isDone ? <CheckCircle2 className="size-5" /> : s.num}
                </div>
                <p
                  className={`mt-2 text-xs font-bold ${isCurrent ? "text-[#312e8e]" : "text-muted-foreground"}`}
                >
                  {s.title}
                </p>
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={`mx-2 h-1 flex-1 rounded-full ${isDone ? "bg-[#10b981]" : "bg-muted"}`}
                />
              )}
            </div>
          );
        })}
      </div>

      <CardContent className="p-8">
        {/* GenericForm = ORQUESTADOR (Mode 4 Hybrid). Mantiene estado + validación + submit.
            La UI de los steps se mantiene — reciben methods del GenericForm. */}
        <GenericForm
          schema={InscripcionPayloadSchema}
          formMethods={form}
          onSubmit={doSubmit}
          skipFooter
          formId="inscripcion-form"
          showErrorsAsToasts
        >
          {({ methods, isSubmitting }) => (
            <>
              {step === 0 && (
                <div className="space-y-4 animate-fade-up">
                  <h3 className="text-lg font-bold text-[#17214b]">
                    {STEPS[0].description}
                  </h3>
                  <Step1Responsable form={methods} />
                </div>
              )}
              {step === 1 && (
                <div className="space-y-4 animate-fade-up">
                  <h3 className="text-lg font-bold text-[#17214b]">
                    {STEPS[1].description}
                  </h3>
                  <Step2Equipo form={methods} />
                </div>
              )}
              {step === 2 && (
                <div className="space-y-4 animate-fade-up">
                  <h3 className="text-lg font-bold text-[#17214b]">
                    {STEPS[2].description}
                  </h3>
                  <Step3Paquete form={methods} />
                </div>
              )}
              {step === 3 && (
                <div className="space-y-4 animate-fade-up">
                  <h3 className="text-lg font-bold text-[#17214b]">
                    {STEPS[3].description}
                  </h3>
                  <div className="flex items-start gap-3 rounded-xl border-2 border-[#f4c64e]/40 bg-[#fff9df] p-4">
                    <Sparkles className="size-5 shrink-0 mt-0.5 text-[#f4c64e]" />
                    <div>
                      <p className="text-sm font-bold text-[#17214b]">
                        Último paso
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Confirma las declaraciones para enviar tu solicitud al
                        Comité.
                      </p>
                    </div>
                  </div>
                  <Step4Declaraciones form={methods} />
                </div>
              )}

              {/* Navigation buttons */}
              <div className="flex items-center justify-between border-t border-border pt-6 mt-6">
                <Button
                  type="button"
                  variant="outline"
                  disabled={step === 0}
                  onClick={() => setStep(step - 1)}
                  className="h-11 rounded-xl px-6"
                >
                  <ChevronLeft className="mr-2 size-4" /> Volver
                </Button>
                {step < STEPS.length - 1 ? (
                  <Button
                    type="button"
                    onClick={next}
                    className="btn-brand-gradient h-11 rounded-xl px-6 font-bold"
                  >
                    Continuar <ChevronRight className="ml-2 size-4" />
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    form="inscripcion-form"
                    disabled={isSubmitting}
                    className="btn-brand-gradient btn-shine h-11 rounded-xl px-8 font-black uppercase tracking-wider"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 size-4 animate-spin" />{" "}
                        Enviando...
                      </>
                    ) : (
                      <>
                        Enviar solicitud{" "}
                        <CheckCircle2 className="ml-2 size-4" />
                      </>
                    )}
                  </Button>
                )}
              </div>
            </>
          )}
        </GenericForm>
      </CardContent>
    </Card>
  );
}
