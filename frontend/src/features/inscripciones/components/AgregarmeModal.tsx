"use client";

import { Loader2, MessageSquare, UserPlus, Users } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";
import { GenericInput } from "@/components/genericForm/GenericInput";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { cn } from "@/lib/utils";
import { useAgregarParticipantes } from "../hooks/useAgregarParticipantes";
import { NOTAS_MAX_LENGTH } from "../schemas/participante.schema";

/**
 * Schema interno: solo rol + notas para el caso "agregarme".
 * La identidad (persona_id) ya viene del usuario autenticado.
 */
const AgregarmeSchema = z.object({
  rol: z.string().min(1, "Rol requerido"),
  notas: z
    .string()
    .max(
      NOTAS_MAX_LENGTH,
      `Las notas no pueden superar los ${NOTAS_MAX_LENGTH} caracteres`,
    )
    .optional()
    .or(z.literal("")),
});

type AgregarmeFormInput = z.input<typeof AgregarmeSchema>;
type AgregarmeFormData = z.output<typeof AgregarmeSchema>;

interface AgregarmeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inscripcionId: string;
  equipoId: string;
  equipoLabel: string;
  user: {
    nombres?: string | null | undefined;
    apellidos?: string | null | undefined;
    email?: string | null | undefined;
  };
  /** ID de la persona asociada al usuario. Si es null, el modal muestra mensaje de error. */
  personaId: string | null;
  onSuccess: () => void;
}

const ROL_OPTIONS = [
  { value: "JUGADOR", label: "Jugador" },
  { value: "CAPITAN", label: "Capitán" },
  { value: "DELEGADO", label: "Delegado" },
];

/**
 * Modal ligero para "agregarme" a un equipo.
 *
 * A diferencia de `AddParticipanteModal`, esta variante no pide datos de
 * identidad: el responsable ya está autenticado y se identifica por
 * `personaId`. Solo selecciona el rol y opcionalmente agrega un comentario
 * interno para el comité.
 */
export function AgregarmeModal({
  open,
  onOpenChange,
  inscripcionId,
  equipoId,
  equipoLabel,
  user,
  personaId,
  onSuccess,
}: AgregarmeModalProps) {
  const mutation = useAgregarParticipantes(inscripcionId, equipoId);
  const [showNotas, setShowNotas] = useState(false);

  const fullName =
    `${user.nombres ?? ""} ${user.apellidos ?? ""}`.trim() ||
    user.email ||
    "Tu persona";

  const initials =
    `${(user.nombres ?? "?").charAt(0)}${(user.apellidos ?? "").charAt(0)}`.toUpperCase();

  const initialData: AgregarmeFormInput = {
    rol: "JUGADOR",
    notas: "",
  };

  async function handleSubmit(data: AgregarmeFormInput) {
    if (!personaId) {
      toast.error(
        "No tienes una persona asociada. Completa tu registro primero.",
      );
      return;
    }
    const output = data as AgregarmeFormData;
    try {
      await mutation.mutateAsync({
        participantes: [
          {
            persona_id: personaId,
            rol: output.rol,
            notas: output.notas?.trim() ? output.notas : null,
          },
        ],
      });
      onSuccess();
      onOpenChange(false);
    } catch {
      // el hook ya muestra el toast de error
    }
  }

  return (
    <AppFormModal<AgregarmeFormInput>
      open={open}
      onOpenChange={onOpenChange}
      title="Agregarme al equipo"
      description={`Vas a registrarte como integrante de "${equipoLabel}".`}
      eyebrow="Inscripción · Auto-registro"
      icon={<UserPlus className="h-5 w-5 text-primary" />}
      primaryLabel="Confirmar y agregarme"
      primaryLoadingLabel="Agregando..."
      primaryLoading={mutation.isPending}
      primaryDisabled={!personaId || mutation.isPending}
      onPrimary={() => {}}
      secondaryLabel="Cancelar"
      preventClose={false}
      schema={AgregarmeSchema}
      initialData={initialData}
      onSubmit={handleSubmit}
      size="md"
      bodyClassName="px-6 sm:px-8 py-6"
    >
      {({ methods }) => {
        const {
          register,
          control,
          watch,
          formState: { errors },
        } = methods;
        const notasValue = String(watch("notas") ?? "");
        const length = notasValue.length;

        return (
          <div className="space-y-5">
            {/* Player context strip */}
            <div className="flex items-center gap-3 rounded-2xl border border-primary/20 bg-primary/[0.04] px-4 py-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/70 text-primary-foreground font-black text-sm shadow-sm">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/70">
                  Tú
                </p>
                <p className="truncate text-sm font-bold text-foreground">
                  {fullName}
                </p>
                {user.email && (
                  <p className="text-xs text-muted-foreground truncate">
                    {user.email}
                  </p>
                )}
              </div>
            </div>

            {!personaId && (
              <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
                <Loader2 className="size-4 text-rose-600 mt-0.5 shrink-0" />
                <div className="text-xs text-rose-700 leading-relaxed">
                  <p className="font-semibold mb-0.5">
                    No tienes una persona asociada
                  </p>
                  <p>
                    Para agregarte, primero vincula tu cuenta a una persona
                    desde tu perfil.
                  </p>
                </div>
              </div>
            )}

            {/* ── Rol ──────────────────────────────────────────────── */}
            <section className="rounded-2xl border border-border/60 bg-sky-50/40 ring-1 ring-sky-200/70 p-5 space-y-4">
              <header className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-sky-600 text-white shadow-sm">
                  <Users className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-black uppercase tracking-wider text-sky-900">
                    Rol en el equipo
                  </h3>
                  <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
                    Define cómo participas en este equipo.
                  </p>
                </div>
              </header>
              <GenericInput
                field={{
                  name: "rol",
                  label: "Rol",
                  type: "select",
                  required: true,
                  options: ROL_OPTIONS,
                  helperText:
                    "Si eres capitán o delegado del equipo, selecciónalo aquí.",
                  containerClassName: "col-span-12",
                }}
                register={register as never}
                control={control as never}
                errors={errors}
              />
            </section>

            {/* ── Comentario / Notas (opcional, colapsable) ────────── */}
            <section
              className={cn(
                "rounded-2xl border border-border/60 ring-1 p-5 space-y-4 transition-colors",
                showNotas
                  ? "bg-violet-50/40 ring-violet-200/70"
                  : "bg-muted/20 ring-transparent",
              )}
            >
              <header className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <div
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white shadow-sm transition-colors",
                      showNotas
                        ? "bg-gradient-to-br from-violet-400 to-violet-600"
                        : "bg-muted-foreground/40",
                    )}
                  >
                    <MessageSquare className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <h3
                      className={cn(
                        "text-sm font-black uppercase tracking-wider",
                        showNotas ? "text-violet-900" : "text-foreground",
                      )}
                    >
                      Comentario para el comité
                    </h3>
                    <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
                      Opcional — agrega una nota interna para el comité si
                      tienes alguna condición médica o algo que comunicar.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNotas((v) => !v)}
                  className={cn(
                    "shrink-0 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider transition-colors",
                    showNotas
                      ? "bg-violet-100 text-violet-800 hover:bg-violet-200"
                      : "bg-muted text-muted-foreground hover:bg-muted/80",
                  )}
                  aria-expanded={showNotas}
                >
                  {showNotas ? "Ocultar" : "Agregar nota"}
                </button>
              </header>

              {showNotas && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label
                      htmlFor="agregarme-notas"
                      className="text-xs font-bold uppercase tracking-wider text-violet-900"
                    >
                      Comentario
                    </Label>
                    <span
                      className={cn(
                        "text-[10px] font-mono font-semibold tabular-nums",
                        length > NOTAS_MAX_LENGTH - 50
                          ? "text-rose-600"
                          : "text-muted-foreground",
                      )}
                    >
                      {length}/{NOTAS_MAX_LENGTH}
                    </span>
                  </div>
                  <Textarea
                    id="agregarme-notas"
                    value={notasValue}
                    onChange={(e) =>
                      methods.setValue("notas", e.target.value, {
                        shouldDirty: true,
                        shouldTouch: true,
                      })
                    }
                    rows={4}
                    maxLength={NOTAS_MAX_LENGTH}
                    placeholder="Ej: Alergia a la penicilina. Lesión previa en rodilla derecha."
                    className="resize-y min-h-[96px] border-violet-200/70 focus-visible:ring-violet-300"
                  />
                  <p className="text-[11px] text-muted-foreground leading-snug">
                    Solo lo verá el comité organizador y el delegado del equipo.
                  </p>
                </div>
              )}
            </section>
          </div>
        );
      }}
    </AppFormModal>
  );
}
