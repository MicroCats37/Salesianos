"use client";

import {
  IdCard,
  MessageSquare,
  Shield,
  UserPlus,
  Users,
} from "lucide-react";
import { GenericInput } from "@/components/genericForm/GenericInput";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { cn } from "@/lib/utils";
import {
  ASEGURADORAS_PERU,
  NOTAS_MAX_LENGTH,
  type ParticipanteFormData,
  type ParticipanteFormInput,
  ParticipanteSchema,
} from "../schemas/participante.schema";
import { DocumentoLookupSmartField } from "./forms/DocumentoLookupSmartField";

interface AddParticipanteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Show the loading state on the primary action. */
  primaryLoading?: boolean;
  /**
   * Receives the validated form data. Returning a promise lets the caller
   * surface a rejection — the modal closes only when the promise resolves.
   */
  onAdd: (data: ParticipanteFormData) => void | Promise<void>;
}

interface SectionProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  badge?: string;
  accent?: "amber" | "sky" | "violet" | "rose" | "emerald";
  children: React.ReactNode;
}

const accentMap: Record<
  NonNullable<SectionProps["accent"]>,
  { ring: string; bg: string; text: string; chip: string; iconBg: string }
> = {
  amber: {
    ring: "ring-amber-200/70",
    bg: "bg-amber-50/40",
    text: "text-amber-900",
    chip: "bg-amber-100 text-amber-800 border-amber-200",
    iconBg: "from-amber-400 to-amber-600",
  },
  sky: {
    ring: "ring-sky-200/70",
    bg: "bg-sky-50/40",
    text: "text-sky-900",
    chip: "bg-sky-100 text-sky-800 border-sky-200",
    iconBg: "from-sky-400 to-sky-600",
  },
  violet: {
    ring: "ring-violet-200/70",
    bg: "bg-violet-50/40",
    text: "text-violet-900",
    chip: "bg-violet-100 text-violet-800 border-violet-200",
    iconBg: "from-violet-400 to-violet-600",
  },
  rose: {
    ring: "ring-rose-200/70",
    bg: "bg-rose-50/40",
    text: "text-rose-900",
    chip: "bg-rose-100 text-rose-800 border-rose-200",
    iconBg: "from-rose-400 to-rose-600",
  },
  emerald: {
    ring: "ring-emerald-200/70",
    bg: "bg-emerald-50/40",
    text: "text-emerald-900",
    chip: "bg-emerald-100 text-emerald-800 border-emerald-200",
    iconBg: "from-emerald-400 to-emerald-600",
  },
};

function Section({
  icon: Icon,
  title,
  description,
  badge,
  accent = "sky",
  children,
}: SectionProps) {
  const a = accentMap[accent];
  return (
    <section
      className={cn(
        "rounded-2xl border border-border/60 ring-1 p-5 space-y-4",
        a.ring,
        a.bg,
      )}
    >
      <header className="flex items-start gap-3">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-sm",
            a.iconBg,
          )}
        >
          <Icon className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3
              className={cn(
                "text-sm font-black uppercase tracking-wider",
                a.text,
              )}
            >
              {title}
            </h3>
            {badge && (
              <span
                className={cn(
                  "inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                  a.chip,
                )}
              >
                {badge}
              </span>
            )}
          </div>
          {description && (
            <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
              {description}
            </p>
          )}
        </div>
      </header>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

/**
 * Modal de pre-registro de un participante en el pool de la inscripción.
 *
 * POOL FIRST: this modal is the ONLY way to register a participant. There is
 * no team context: the preregistration is submitted WITHOUT `equipo_id`, so
 * the backend creates the `InscripcionPersona` and claims the paid cup when
 * there is free capacity. Placing the participant in a team is a later,
 * separate action (the team selector).
 *
 * UI/UX: secciones con jerarquía visual clara (iconos, badges, helper texts),
 * checkboxes con feedback visual de selección, campo de notas con contador,
 * contexto visible (el pool) y declaraciones agrupadas.
 *
 * The team-only fields (rol and talla) are NOT asked: the preregistration
 * endpoint does not accept them — no data that the backend would discard.
 */
export function AddParticipanteModal({
  open,
  onOpenChange,
  primaryLoading = false,
  onAdd,
}: AddParticipanteModalProps) {
  const initialData: ParticipanteFormInput = {
    tipoDocumento: "DNI",
    numeroDocumento: "",
    nombres: "",
    apellidos: "",
    genero: "M",
    rol: "J",
    telefono: "",
    whatsapp: "",
    talla_camiseta: "",
    aseguradora_nombre: "",
    notas: "",
  };

  async function handleSubmit(data: ParticipanteFormInput) {
    // Awaited so a caller rejection (e.g. a backend capacity error) is
    // handled before the modal decides to close.
    await onAdd(data as ParticipanteFormData);
  }

  return (
    <AppFormModal<ParticipanteFormInput>
      open={open}
      onOpenChange={onOpenChange}
      title="Pre-registrar Participante"
      description="Vas a pre-registrar a un participante en el pool de la inscripción. Quedará esperando un cupo pagado para poder entrar a un equipo."
      eyebrow="Inscripción · Pre-registro"
      icon={<UserPlus className="h-5 w-5 text-primary" />}
      primaryLabel="Agregar al pool"
      primaryLoadingLabel="Registrando..."
      primaryLoading={primaryLoading}
      onPrimary={() => {}}
      secondaryLabel="Cancelar"
      schema={ParticipanteSchema}
      initialData={initialData}
      onSubmit={handleSubmit}
      size="lg"
      bodyClassName="px-6 sm:px-8 py-6"
    >
      {({ methods }) => {
        const {
          register,
          control,
          setValue,
          watch,
          formState: { errors },
        } = methods;
        const notasValue = String(watch("notas") ?? "");

        return (
          <div className="space-y-5">
            {/* Destino: el dato (DÓNDE va), no otra explicación. El porqué
                ya está en la descripción del modal. */}
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/[0.04] px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.15em] text-primary">
                <Users className="size-3.5" />
                Destino: pool de participantes
              </span>
            </div>

            {/* ── Identidad ──────────────────────────────────────────── */}
            <Section
              icon={IdCard}
              title="Identidad"
              description="Autocompleta los datos con el DNI."
              badge="Obligatorio"
              accent="sky"
            >
              <div className="grid grid-cols-12 gap-3">
                <GenericInput
                  field={{
                    name: "tipoDocumento",
                    label: "Tipo de Doc.",
                    type: "select",
                    options: [
                      { label: "DNI", value: "DNI" },
                      { label: "CE", value: "CE" },
                      { label: "Pasaporte", value: "PAS" },
                    ],
                    containerClassName: "col-span-12 sm:col-span-4",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <DocumentoLookupSmartField />
                <GenericInput
                  field={{
                    name: "nombres",
                    label: "Nombres",
                    type: "text",
                    required: true,
                    placeholder: "Ej. Juan Carlos",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "apellidos",
                    label: "Apellidos",
                    type: "text",
                    required: true,
                    placeholder: "Ej. Pérez López",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "genero",
                    label: "Género",
                    type: "select",
                    required: true,
                    options: [
                      { label: "Masculino", value: "M" },
                      { label: "Femenino", value: "F" },
                    ],
                    containerClassName: "col-span-12",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
              </div>
            </Section>

            {/* ── Contacto ──────────────────────────────────────────── */}
            <Section
              icon={Users}
              title="Contacto"
              description="Opcional. Para que el comité pueda ubicarla."
              accent="amber"
            >
              <div className="grid grid-cols-12 gap-3">
                <GenericInput
                  field={{
                    name: "telefono",
                    label: "Teléfono",
                    type: "text",
                    placeholder: "9 dígitos",
                    helperText: "9 dígitos sin prefijo",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "whatsapp",
                    label: "WhatsApp",
                    type: "text",
                    placeholder: "9 dígitos",
                    helperText: "9 dígitos",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                {/* Rol y talla son conceptos de equipo: el preregistro al pool
                    no los acepta, así que no se piden. */}
              </div>
            </Section>

            {/* ── Seguro Médico ──────────────────────────────────────── */}
            <Section
              icon={Shield}
              title="Seguro Médico"
              description="Opcional. Datos de la póliza."
              accent="emerald"
            >
              <div className="grid grid-cols-12 gap-3">
                <GenericInput
                  field={{
                    name: "aseguradora_nombre",
                    label: "Aseguradora",
                    type: "select",
                    placeholder: "Ninguna / No especifica",
                    options: ASEGURADORAS_PERU.map((a) => ({
                      label: a.label,
                      value: a.value,
                    })),
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "aseguradora_numero_poliza",
                    label: "Número de Póliza",
                    type: "text",
                    placeholder: "Ej: 123456",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
              </div>
            </Section>

            {/* ── Notas ──────────────────────────────────────────────── */}
            <Section
              icon={MessageSquare}
              title="Notas internas"
              description="Alergias, condiciones médicas u observaciones."
              accent="violet"
            >
              <NotasTextarea
                value={notasValue}
                onChange={(v) =>
                  setValue("notas", v, { shouldDirty: true, shouldTouch: true })
                }
                error={errors.notas?.message as string | undefined}
              />
            </Section>

            {/* Sin pie: la descripción del modal ya explica el destino y el
                espera del cupo pagado. Repetirlo por tercera vez solo
                alargaba el formulario. */}
          </div>
        );
      }}
    </AppFormModal>
  );
}

type NotasTextareaProps = {
  value: string;
  onChange: (value: string) => void;
  error?: string | undefined;
};

function NotasTextarea({ value, onChange, error }: NotasTextareaProps) {
  const length = value?.length ?? 0;
  const nearLimit = length > NOTAS_MAX_LENGTH - 50;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <Label
          htmlFor="notas"
          className="text-xs font-bold uppercase tracking-wider text-violet-900"
        >
          Notas (opcional)
        </Label>
        <span
          className={cn(
            "text-[10px] font-mono font-semibold tabular-nums",
            nearLimit ? "text-rose-600" : "text-muted-foreground",
          )}
        >
          {length}/{NOTAS_MAX_LENGTH}
        </span>
      </div>
      <Textarea
        id="notas"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        maxLength={NOTAS_MAX_LENGTH}
        placeholder="Ej: Alergia a la penicilina. Tratamiento médico vigente. Lesión previa en rodilla derecha."
        aria-invalid={!!error}
        className={cn(
          "resize-y min-h-[96px] border-violet-200/70 focus-visible:ring-violet-300",
          error && "border-rose-400 ring-1 ring-rose-300",
        )}
      />
      {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}
      <p className="text-[11px] text-muted-foreground leading-snug">
        Solo lo verá el comité organizador y el delegado del equipo.
      </p>
    </div>
  );
}
