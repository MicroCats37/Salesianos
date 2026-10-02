"use client";

import {
  AlertTriangle,
  Info,
  MessageSquare,
  Shield,
  Shirt,
  UserCog,
  Users,
} from "lucide-react";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { GenericInput } from "@/components/genericForm/GenericInput";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useEditarParticipante } from "../hooks/useEditarParticipante";
import {
  EditarParticipanteSchema,
  NOTAS_MAX_LENGTH,
  ROLES_PERMITIDOS,
  TALLES_PERMITIDOS,
  type EditarParticipanteFormData,
} from "../schemas/participanteEdit.schema";
import { ASEGURADORAS_PERU } from "../schemas/participante.schema";
import type { ParticipanteOut } from "../services/inscripcion.service";

interface EditParticipanteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inscripcionId: string;
  participante: ParticipanteOut | null;
  equipoLabel: string;
  onSuccess: () => void;
}

const ROL_LABEL: Record<string, string> = {
  JUGADOR: "Jugador",
  CAPITAN: "Capitán",
  DELEGADO: "Delegado",
};

/**
 * Modal para editar la asignación de un participante dentro de un equipo
 * (rol, talle_camiseta, aseguradora, notas y aceptaciones).
 *
 * Usa `AppFormModal` + `GenericInput` y aplica el schema
 * `EditarParticipanteSchema` con `superRefine`.
 */
export function EditParticipanteModal({
  open,
  onOpenChange,
  inscripcionId,
  participante,
  equipoLabel,
  onSuccess,
}: EditParticipanteModalProps) {
  const mutation = useEditarParticipante(
    inscripcionId,
    participante?.id ?? "",
  );

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) onOpenChange(false);
  }

  if (!participante) return null;

  const initialData: EditarParticipanteFormData = {
    rol: participante.rol ?? "JUGADOR",
    talle_camiseta: participante.talle_camiseta ?? "",
    aseguradora_nombre: participante.persona?.aseguradora_nombre ?? "",
    aseguradora_numero_poliza: participante.persona?.aseguradora_numero_poliza ?? "",
    notas: participante.notas ?? "",
  };

  async function handleSubmit(data: EditarParticipanteFormData) {
    const payload = {
      rol: data.rol,
      talle_camiseta: data.talle_camiseta || null,
      aseguradora_nombre: data.aseguradora_nombre || null,
      aseguradora_numero_poliza: data.aseguradora_numero_poliza || null,
      notas: data.notas || null,
    };
    await mutation.mutateAsync(payload);
    onSuccess();
    handleOpenChange(false);
  }

  const fullName = `${participante.persona.nombres} ${participante.persona.apellidos}`;

  return (
    <AppFormModal<EditarParticipanteFormData>
      open={open}
      onOpenChange={handleOpenChange}
      title="Editar jugador"
      description={`Modifica los datos de ${fullName} en el equipo "${equipoLabel}".`}
      eyebrow="Inscripción · Edición"
      icon={<UserCog className="h-5 w-5 text-primary" />}
      primaryLabel="Guardar cambios"
      primaryLoadingLabel="Guardando..."
      primaryLoading={mutation.isPending}
      onPrimary={() => {}}
      secondaryLabel="Cancelar"
      preventClose={false}
      schema={EditarParticipanteSchema}
      initialData={initialData}
      onSubmit={handleSubmit}
      size="lg"
      bodyClassName="px-6 sm:px-8 py-6"
    >
      {({ methods }) => {
        const { register, control, watch, setValue, formState: { errors } } = methods;
        const notasValue = watch("notas") ?? "";
        const length = notasValue.length;

        return (
          <div className="space-y-5">
            {/* Player context strip */}
            <div className="flex items-center gap-3 rounded-2xl border border-primary/20 bg-primary/[0.04] px-4 py-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/70 text-primary-foreground font-black text-sm shadow-sm">
                {participante.persona.nombres.charAt(0)}
                {participante.persona.apellidos.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/70">
                  Jugador
                </p>
                <p className="truncate text-sm font-bold text-foreground">
                  {fullName}
                </p>
                <p className="text-xs text-muted-foreground">
                  {participante.persona.numero_documento}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                  participante.rol === "CAPITAN"
                    ? "bg-amber-100 text-amber-800"
                    : participante.rol === "DELEGADO"
                      ? "bg-violet-100 text-violet-800"
                      : "bg-sky-100 text-sky-800",
                )}
              >
                {ROL_LABEL[participante.rol] ?? participante.rol}
              </span>
            </div>

            {/* ── Rol y Talle ───────────────────────────────────────── */}
            <section className="rounded-2xl border border-border/60 bg-sky-50/40 ring-1 ring-sky-200/70 p-5 space-y-4">
              <header className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-sky-600 text-white shadow-sm">
                  <Users className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-black uppercase tracking-wider text-sky-900">
                    Rol y Talle
                  </h3>
                  <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
                    Define la función del jugador en el equipo y su talle de camiseta.
                  </p>
                </div>
              </header>
              <div className="grid grid-cols-2 gap-3">
                <GenericInput
                  field={{
                    name: "rol",
                    label: "Rol en el equipo",
                    type: "select",
                    required: true,
                    options: ROLES_PERMITIDOS.map((r) => ({
                      value: r,
                      label: ROL_LABEL[r] ?? r,
                    })),
                    containerClassName: "col-span-2 sm:col-span-1",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "talle_camiseta",
                    label: "Talle camiseta",
                    type: "select",
                    placeholder: "Sin talle",
                    options: TALLES_PERMITIDOS.map((t) => ({
                      value: t,
                      label: t,
                    })),
                    helperText: "Para entrega del polo oficial",
                    containerClassName: "col-span-2 sm:col-span-1",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
              </div>
            </section>

            {/* ── Seguro Médico ──────────────────────────────────────── */}
            <section className="rounded-2xl border border-border/60 bg-emerald-50/40 ring-1 ring-emerald-200/70 p-5 space-y-4">
              <header className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-white shadow-sm">
                  <Shield className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-black uppercase tracking-wider text-emerald-900">
                    Seguro Médico
                  </h3>
                  <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
                    Datos del seguro médico del participante (opcional).
                  </p>
                </div>
              </header>
              <div className="grid grid-cols-2 gap-3">
                <GenericInput
                  field={{
                    name: "aseguradora_nombre",
                    label: "Aseguradora",
                    type: "select",
                    placeholder: "Sin seguro",
                    options: ASEGURADORAS_PERU.map((a) => ({
                      value: a.value,
                      label: a.label,
                    })),
                    containerClassName: "col-span-2 sm:col-span-1",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "aseguradora_numero_poliza",
                    label: "N° de póliza",
                    type: "text",
                    placeholder: "Número de póliza",
                    containerClassName: "col-span-2 sm:col-span-1",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
              </div>
            </section>

            {/* ── Notas ─────────────────────────────────────────────── */}
            <section className="rounded-2xl border border-border/60 bg-violet-50/40 ring-1 ring-violet-200/70 p-5 space-y-4">
              <header className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-400 to-violet-600 text-white shadow-sm">
                  <MessageSquare className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-black uppercase tracking-wider text-violet-900">
                    Notas internas
                  </h3>
                  <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
                    Información adicional para el comité (alergias, observaciones).
                  </p>
                </div>
              </header>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label
                    htmlFor="notas-edit"
                    className="text-xs font-bold uppercase tracking-wider text-violet-900"
                  >
                    Notas (opcional)
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
                  id="notas-edit"
                  value={notasValue}
                  onChange={(e) =>
                    setValue("notas", e.target.value, {
                      shouldDirty: true,
                      shouldTouch: true,
                    })
                  }
                  rows={4}
                  maxLength={NOTAS_MAX_LENGTH}
                  placeholder="Ej: Alergia a la penicilina. Tratamiento médico vigente."
                  aria-invalid={!!errors.notas}
                  className={cn(
                    "resize-y min-h-[96px] border-violet-200/70 focus-visible:ring-violet-300",
                    errors.notas && "border-rose-400 ring-1 ring-rose-300",
                  )}
                />
                {errors.notas && (
                  <p className="text-xs text-rose-600 font-medium">
                    {errors.notas.message as string}
                  </p>
                )}
                <p className="text-[11px] text-muted-foreground leading-snug">
                  Solo lo verá el comité organizador y el delegado del equipo.
                </p>
              </div>
            </section>

            {/* ── Footer hint ───────────────────────────────────────── */}
            <div className="flex items-start gap-2 rounded-xl border border-sky-200/60 bg-sky-50/40 p-3">
              <Info className="size-4 text-sky-700 mt-0.5 shrink-0" />
              <p className="text-xs text-sky-900 leading-relaxed">
                Los cambios se aplican a este equipo y disciplina
                inmediatamente. Para mover al jugador entre equipos usa el
                <Shirt className="inline size-3 mx-1 align-text-bottom" />
                arrastre en la lista del equipo.
              </p>
            </div>

            {mutation.isError && (
              <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
                <AlertTriangle className="size-4 text-rose-600 mt-0.5 shrink-0" />
                <p className="text-xs text-rose-700 leading-relaxed">
                  {mutation.error instanceof Error
                    ? mutation.error.message
                    : "No se pudo guardar el jugador."}
                </p>
              </div>
            )}
          </div>
        );
      }}
    </AppFormModal>
  );
}