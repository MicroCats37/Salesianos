"use client";

import {
  AlertTriangle,
  FileSignature,
  IdCard,
  IdCardLanyard,
  Info,
  MessageSquare,
  Package,
  Shield,
  Sparkles,
  Stethoscope,
  UserPlus,
  Users,
} from "lucide-react";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { GenericInput } from "@/components/genericForm/GenericInput";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  ASEGURADORAS_PERU,
  NOTAS_MAX_LENGTH,
  type ParticipanteFormData,
  type ParticipanteFormInput,
} from "../schemas/participante.schema";
import { ParticipanteSchema } from "../schemas/participante.schema";
import { DocumentoLookupSmartField } from "./forms/DocumentoLookupSmartField";

interface AddParticipanteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  equipoId: string;
  equipoLabel: string;
  onAdd: (data: ParticipanteFormData) => void;
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
            <h3 className={cn("text-sm font-black uppercase tracking-wider", a.text)}>
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

interface CheckboxRowProps {
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: "amber" | "rose" | "violet";
  value: boolean | undefined;
  onChange: (checked: boolean) => void;
}

function CheckboxRow({
  label,
  description,
  icon: Icon,
  accent,
  value,
  onChange,
}: CheckboxRowProps) {
  const checked = value === true;
  const palettes: Record<typeof accent, { ring: string; bg: string; iconBg: string; text: string }> = {
    amber: {
      ring: "ring-amber-200",
      bg: "bg-amber-50/60",
      iconBg: "bg-amber-100 text-amber-700",
      text: "text-amber-900",
    },
    rose: {
      ring: "ring-rose-200",
      bg: "bg-rose-50/60",
      iconBg: "bg-rose-100 text-rose-700",
      text: "text-rose-900",
    },
    violet: {
      ring: "ring-violet-200",
      bg: "bg-violet-50/60",
      iconBg: "bg-violet-100 text-violet-700",
      text: "text-violet-900",
    },
  };
  const p = palettes[accent];
  return (
    <label
      className={cn(
        "group flex items-start gap-3 rounded-xl border border-border/60 p-3 cursor-pointer transition-all duration-150",
        checked
          ? cn("ring-2", p.ring, p.bg)
          : "ring-1 ring-transparent hover:border-border hover:bg-muted/30",
      )}
    >
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
          checked ? p.iconBg : "bg-muted text-muted-foreground",
        )}
      >
        <Icon className="size-4" />
      </div>
      <div className="flex-1 min-w-0 pt-0.5">
        <p
          className={cn(
            "text-sm font-semibold leading-tight",
            checked ? p.text : "text-foreground",
          )}
        >
          {label}
        </p>
        <p className="text-xs text-muted-foreground leading-snug mt-0.5">
          {description}
        </p>
      </div>
      <Checkbox
        checked={checked}
        onCheckedChange={(v) => onChange(Boolean(v))}
        aria-label={label}
        className="mt-1 shrink-0"
      />
    </label>
  );
}

/**
 * Modal para agregar un participante a un equipo.
 *
 * UI/UX: secciones con jerarquía visual clara (iconos, badges, helper texts),
 * checkboxes con feedback visual de selección, campo de notas con contador,
 * contexto del equipo visible y declaraciones agrupadas.
 */
export function AddParticipanteModal({
  open,
  onOpenChange,
  equipoId,
  equipoLabel,
  onAdd,
}: AddParticipanteModalProps) {
  // equipoId is part of the public contract but the modal body resolves
  // everything through `equipoLabel`. Keep the destructure so existing
  // callers (e.g. InscripcionDetailView) keep working.
  void equipoId;
  const initialData: ParticipanteFormInput = {
    tipoDocumento: "DNI",
    numeroDocumento: "",
    nombres: "",
    apellidos: "",
    genero: "M",
    rol: "JUGADOR",
    telefono: "",
    whatsapp: "",
    talle_camiseta: "",
    aseguradora_nombre: "",
    notas: "",
    acepto_bases: false,
    acepto_aptitud_fisica: false,
    acepto_imagen: false,
  };

  async function handleSubmit(data: ParticipanteFormInput) {
    onAdd(data as ParticipanteFormData);
  }

  return (
    <AppFormModal<ParticipanteFormInput>
      open={open}
      onOpenChange={onOpenChange}
      title="Agregar Participante"
      description={`Vas a registrar un nuevo integrante en el equipo "${equipoLabel}".`}
      eyebrow="Inscripción · Nuevo integrante"
      icon={<UserPlus className="h-5 w-5 text-primary" />}
      primaryLabel="Agregar al equipo"
      primaryLoadingLabel="Agregando..."
      onPrimary={() => {}}
      secondaryLabel="Cancelar"
      schema={ParticipanteSchema}
      initialData={initialData}
      onSubmit={handleSubmit}
      size="lg"
      bodyClassName="px-6 sm:px-8 py-6"
    >
      {({ methods }) => {
        const { register, control, setValue, watch, formState: { errors } } = methods;
        const notasValue = String(watch("notas") ?? "");

        return (
          <div className="space-y-5">
            {/* Team context strip */}
            <div className="flex items-center gap-3 rounded-2xl border border-primary/20 bg-primary/[0.04] px-4 py-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Package className="size-4" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/70">
                  Equipo destino
                </p>
                <p className="truncate text-sm font-bold text-foreground">
                  {equipoLabel}
                </p>
              </div>
            </div>

            {/* ── Identidad ──────────────────────────────────────────── */}
            <Section
              icon={IdCard}
              title="Identidad"
              description="Datos de identidad del participante. Puedes autocompletar con DNI."
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

            {/* ── Contacto y Rol ─────────────────────────────────────── */}
            <Section
              icon={Users}
              title="Contacto y Rol"
              description="Datos de contacto opcionales y rol dentro del equipo."
              accent="amber"
            >
              <div className="grid grid-cols-12 gap-3">
                <GenericInput
                  field={{
                    name: "telefono",
                    label: "Teléfono",
                    type: "text",
                    placeholder: "9 dígitos",
                    helperText: "Opcional — 9 dígitos sin prefijo",
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
                    helperText: "Opcional — para contacto rápido del comité",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "rol",
                    label: "Rol en el equipo",
                    type: "select",
                    required: true,
                    options: [
                      { label: "Jugador", value: "JUGADOR" },
                      { label: "Capitán", value: "CAPITAN" },
                      { label: "Delegado", value: "DELEGADO" },
                    ],
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
                <GenericInput
                  field={{
                    name: "talle_camiseta",
                    label: "Talle de Camiseta",
                    type: "select",
                    placeholder: "Sin talle",
                    options: [
                      { label: "XS", value: "XS" },
                      { label: "S", value: "S" },
                      { label: "M", value: "M" },
                      { label: "L", value: "L" },
                      { label: "XL", value: "XL" },
                      { label: "XXL", value: "XXL" },
                    ],
                    helperText: "Opcional — para entrega del polo oficial",
                    containerClassName: "col-span-12 sm:col-span-6",
                  }}
                  register={register as never}
                  control={control as never}
                  errors={errors}
                />
              </div>
            </Section>

            {/* ── Seguro Médico ──────────────────────────────────────── */}
            <Section
              icon={Shield}
              title="Seguro Médico"
              description="Datos del seguro médico del participante (opcional)."
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
              description="Información adicional que el comité debe conocer (alergias, condiciones médicas, observaciones)."
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

            {/* ── Declaraciones Obligatorias ─────────────────────────── */}
            <Section
              icon={FileSignature}
              title="Declaraciones Obligatorias"
              description="El equipo debe aceptar las bases y compromisos del evento."
              badge="Requerido"
              accent="amber"
            >
              <div className="space-y-3">
                <CheckboxRow
                  icon={Sparkles}
                  accent="amber"
                  label="Acepto las bases del evento"
                  description="Bases del campeonato, reglamento y protocolo de competencia."
                  value={watch("acepto_bases")}
                  onChange={(v) =>
                    setValue("acepto_bases", v, {
                      shouldValidate: true,
                      shouldDirty: true,
                      shouldTouch: true,
                    })
                  }
                />
                <CheckboxRow
                  icon={Stethoscope}
                  accent="rose"
                  label="Certificado de aptitud física"
                  description="Certifico que el participante está física y mentalmente apto. Adjunto certificado médico si aplica."
                  value={watch("acepto_aptitud_fisica")}
                  onChange={(v) =>
                    setValue("acepto_aptitud_fisica", v, {
                      shouldValidate: true,
                      shouldDirty: true,
                      shouldTouch: true,
                    })
                  }
                />
                <CheckboxRow
                  icon={IdCardLanyard}
                  accent="violet"
                  label="Autorización de uso de imagen"
                  description="Autorizo el uso de mi imagen en fotografías y videos del evento con fines de difusión."
                  value={watch("acepto_imagen")}
                  onChange={(v) =>
                    setValue("acepto_imagen", v, {
                      shouldValidate: true,
                      shouldDirty: true,
                      shouldTouch: true,
                    })
                  }
                />
              </div>
              <div className="flex items-start gap-2 rounded-xl border border-amber-200/60 bg-amber-50/50 p-3">
                <AlertTriangle className="size-4 text-amber-600 mt-0.5 shrink-0" />
                <p className="text-xs text-amber-900 leading-relaxed">
                  Las tres declaraciones son obligatorias para registrar al
                  participante en el equipo.
                </p>
              </div>
            </Section>

            {/* ── Footer info ────────────────────────────────────────── */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
              <Info className="size-3.5" />
              <p>
                El participante se agregará a la lista de borradores del equipo.
                Pulsa <span className="font-semibold text-foreground">"Agregar al equipo"</span> para
                guardarlo en la inscripción.
              </p>
            </div>
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
      {error && (
        <p className="text-xs text-rose-600 font-medium">{error}</p>
      )}
      <p className="text-[11px] text-muted-foreground leading-snug">
        Solo lo verá el comité organizador y el delegado del equipo.
      </p>
    </div>
  );
}