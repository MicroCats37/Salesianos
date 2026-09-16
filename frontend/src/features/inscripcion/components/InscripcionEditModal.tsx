"use client";

import {
  AlertTriangle,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  Trophy,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { notify } from "@/errors";
import { stripNonDigits } from "@/lib/utils";
import type { MyInscripcion } from "../hooks/useMyInscripcion";
import { useUpdateInscripcion } from "../hooks/useUpdateInscripcion";
import {
  type DeportistaEditData,
  DeportistaEditSchema,
} from "../schemas/deportista-edit.schema";
import { getDisciplinas } from "../services/catalog.service";

// ─── Constants ────────────────────────────────────────────────────────────────

const TALLAS = ["XS", "S", "M", "L", "XL", "XXL"] as const;
const ROLES = ["Jugador", "Capitán", "Delegado"] as const;
const ACREDITACIONES = [
  "Verificación en padrón",
  "Excepción aprobada",
] as const;
const TIPOS_DOCUMENTO = ["DNI", "CE", "PAS"] as const;

type Talla = (typeof TALLAS)[number];
type Rol = (typeof ROLES)[number];
type Acreditacion = (typeof ACREDITACIONES)[number];
type TipoDocumento = (typeof TIPOS_DOCUMENTO)[number];

function toTalla(value: string | null | undefined): Talla | null {
  return TALLAS.includes(value as Talla) ? (value as Talla) : null;
}

function toAcreditacion(value: string | null | undefined): Acreditacion {
  return ACREDITACIONES.includes(value as Acreditacion)
    ? (value as Acreditacion)
    : "Verificación en padrón";
}

function toRol(value: string | null | undefined): Rol {
  return ROLES.includes(value as Rol) ? (value as Rol) : "Jugador";
}

function toTipoDocumento(value: string | null | undefined): TipoDocumento {
  return TIPOS_DOCUMENTO.includes(value as TipoDocumento)
    ? (value as TipoDocumento)
    : "DNI";
}

function toGenero(value: string | null | undefined): "V" | "M" | null {
  return value === "V" || value === "M" ? value : null;
}

// ─── Types ───────────────────────────────────────────────────────────────────

type DisciplinaOption = {
  id: string;
  nombre: string;
};

type AddPlayerPayload = {
  tipoDocumento: TipoDocumento;
  numeroDocumento: string;
  nombres: string;
  apellidos: string;
  genero: "V" | "M" | null;
  telefono: string | null;
  rolDisciplina: Rol;
  acreditacion: Acreditacion;
  disciplinaIds: string[];
  shirtSize: Talla | null;
};

interface InscripcionEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inscripcion: MyInscripcion;
  onSuccess?: () => void;
}

// ─── Shared atoms ────────────────────────────────────────────────────────────

interface FieldErrorProps {
  message?: string;
}
function FieldError({ message }: FieldErrorProps) {
  if (!message) return null;
  return (
    <p className="mt-1 flex items-start gap-1 text-[11px] font-medium text-red-500">
      <AlertTriangle className="mt-0.5 size-3 shrink-0" />
      <span className="min-w-0 break-words">{message}</span>
    </p>
  );
}

interface LabeledFieldProps {
  label: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}
function LabeledField({
  label,
  error,
  children,
  className,
}: LabeledFieldProps) {
  return (
    <div className={`flex min-w-0 flex-col gap-1.5 ${className ?? ""}`}>
      <Label className="text-xs font-semibold text-muted-foreground">
        {label}
      </Label>
      {children}
      <FieldError message={error} />
    </div>
  );
}

// ─── Team name ───────────────────────────────────────────────────────────────

interface EditTeamNameFieldProps {
  value: string;
  onChange: (value: string) => void;
}
function EditTeamNameField({ value, onChange }: EditTeamNameFieldProps) {
  return (
    <LabeledField label="Nombre del equipo">
      <div className="relative">
        <Trophy className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#312e8e]" />
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="input-brand w-full bg-white pl-9"
          placeholder="Ej. Los Invictos 2002"
        />
      </div>
    </LabeledField>
  );
}

// ─── Discipline tabs ─────────────────────────────────────────────────────────

interface DisciplineTabsProps {
  disciplinas: DisciplinaOption[];
  activeDisc: string | null;
  onSelect: (id: string) => void;
}
function DisciplineTabs({
  disciplinas,
  activeDisc,
  onSelect,
}: DisciplineTabsProps) {
  if (disciplinas.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/20 bg-muted/30 p-3 text-center text-xs italic text-muted-foreground">
        No hay disciplinas disponibles para esta inscripción.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Label className="text-xs font-bold uppercase text-muted-foreground">
        Disciplina
      </Label>
      <div className="-mx-1 flex w-full gap-2 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {disciplinas.map((disc) => {
          const isActive = activeDisc === disc.id;
          return (
            <button
              key={disc.id}
              type="button"
              onClick={() => onSelect(disc.id)}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-bold transition ${
                isActive
                  ? "border-[#312e8e] bg-[#312e8e] text-white shadow"
                  : "border-border bg-white text-[#312e8e] hover:border-[#312e8e]/40"
              }`}
            >
              {disc.nombre}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Current roster ──────────────────────────────────────────────────────────

interface CurrentRosterListProps {
  deportistas: DeportistaEditData[];
  activeDisc: string | null;
  onRemove: (docNum: string, discId: string) => void;
}
function CurrentRosterList({
  deportistas,
  activeDisc,
  onRemove,
}: CurrentRosterListProps) {
  const filtered = useMemo(() => {
    if (!activeDisc) return [];
    return deportistas.filter((d) => d.disciplinaIds.includes(activeDisc));
  }, [deportistas, activeDisc]);

  if (filtered.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/20 bg-muted/30 p-4 text-center">
        <p className="text-sm italic text-muted-foreground">
          Aún no hay deportistas en esta disciplina.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {filtered.map((d) => (
        <div
          key={`${d.tipoDocumento}-${d.numeroDocumento}`}
          className="flex w-full items-start justify-between gap-3 rounded-lg border border-border bg-white p-3 shadow-sm"
        >
          <div className="flex min-w-0 flex-1 items-start gap-3">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#312e8e]/10 text-xs font-bold text-[#312e8e]">
              <Users className="size-3.5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="break-words text-sm font-bold text-[#17214b]">
                {d.apellidos}, {d.nombres}
              </p>
              <p className="break-words text-xs text-muted-foreground">
                {d.tipoDocumento}: {d.numeroDocumento}
              </p>
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span>{d.rolDisciplina}</span>
                <span>Talla: {d.shirtSize ?? "—"}</span>
                <span>{d.acreditacion}</span>
              </div>
            </div>
          </div>
          {activeDisc && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 text-red-500 hover:bg-red-50 hover:text-red-600"
              onClick={() => onRemove(d.numeroDocumento, activeDisc)}
            >
              <Trash2 className="size-4" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Add player panel ────────────────────────────────────────────────────────

interface AddDeportistaPanelProps {
  activeDisc: string | null;
  activeDiscName: string;
  onAdd: (data: AddPlayerPayload) => boolean;
  errors: Record<string, string>;
}
function AddDeportistaPanel({
  activeDisc,
  activeDiscName,
  onAdd,
  errors,
}: AddDeportistaPanelProps) {
  const [tipoDocumento, setTipoDocumento] = useState<TipoDocumento>("DNI");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [nombres, setNombres] = useState("");
  const [apellidos, setApellidos] = useState("");
  const [genero, setGenero] = useState<"V" | "M" | "">("");
  const [telefono, setTelefono] = useState("");
  const [rolDisciplina, setRolDisciplina] = useState<Rol>("Jugador");
  const [acreditacion, setAcreditacion] = useState<Acreditacion>(
    "Verificación en padrón",
  );
  const [shirtSize, setShirtSize] = useState<Talla>("M");

  const resetForm = () => {
    setNumeroDocumento("");
    setNombres("");
    setApellidos("");
    setGenero("");
    setTelefono("");
  };

  const handleSubmit = () => {
    if (!activeDisc) return;

    const added = onAdd({
      tipoDocumento,
      numeroDocumento: numeroDocumento.trim(),
      nombres: nombres.trim(),
      apellidos: apellidos.trim(),
      genero: genero || null,
      telefono: telefono.trim() || null,
      rolDisciplina,
      acreditacion,
      disciplinaIds: [activeDisc],
      shirtSize,
    });

    // Only clear the form when the player was actually added.
    // This prevents losing typed data when validation fails.
    if (added) resetForm();
  };

  if (!activeDisc) {
    return (
      <div className="rounded-xl border border-dashed border-muted-foreground/20 bg-muted/30 p-4 text-center">
        <p className="text-sm italic text-muted-foreground">
          Selecciona una disciplina para añadir deportistas.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl border border-[#312e8e]/15 bg-[#f4f6fb] p-3 sm:p-4">
      <h4 className="flex flex-wrap items-center gap-2 text-sm font-bold text-[#312e8e]">
        <Plus className="size-4 shrink-0" />
        <span className="min-w-0 break-words">
          Añadir deportista a {activeDiscName}
        </span>
      </h4>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <LabeledField label="Tipo Doc" error={errors.tipoDocumento}>
          <Select
            value={tipoDocumento}
            onValueChange={(v) => setTipoDocumento(toTipoDocumento(v))}
          >
            <SelectTrigger className="w-full bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIPOS_DOCUMENTO.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </LabeledField>

        <LabeledField label="Número Doc" error={errors.numeroDocumento}>
          <Input
            className={`w-full bg-white ${
              errors.numeroDocumento
                ? "border-red-500 focus-visible:ring-red-500"
                : ""
            }`}
            value={numeroDocumento}
            onChange={(e) => {
              const val = e.target.value;
              if (tipoDocumento === "PAS") {
                // PAS: keep alphanumeric only, no max limit here (schema enforces min 4)
                setNumeroDocumento(val.replace(/[^a-zA-Z0-9]/g, ""));
              } else {
                // DNI/CE: digits only, enforce max length
                setNumeroDocumento(
                  stripNonDigits(val).slice(0, tipoDocumento === "CE" ? 9 : 8),
                );
              }
            }}
            inputMode={tipoDocumento === "DNI" ? "numeric" : "text"}
            maxLength={
              tipoDocumento === "DNI"
                ? 8
                : tipoDocumento === "CE"
                  ? 9
                  : undefined
            }
            placeholder={
              tipoDocumento === "DNI"
                ? "12345678"
                : tipoDocumento === "CE"
                  ? "123456789"
                  : "Alphanumeric"
            }
          />
        </LabeledField>

        <LabeledField label="Nombres" error={errors.nombres}>
          <Input
            className={`w-full bg-white ${
              errors.nombres ? "border-red-500 focus-visible:ring-red-500" : ""
            }`}
            value={nombres}
            onChange={(e) => setNombres(e.target.value)}
            placeholder="Nombres completos"
          />
        </LabeledField>

        <LabeledField label="Apellidos" error={errors.apellidos}>
          <Input
            className={`w-full bg-white ${
              errors.apellidos
                ? "border-red-500 focus-visible:ring-red-500"
                : ""
            }`}
            value={apellidos}
            onChange={(e) => setApellidos(e.target.value)}
            placeholder="Apellidos completos"
          />
        </LabeledField>

        <LabeledField label="Género" error={errors.genero}>
          <Select
            value={genero}
            onValueChange={(v) => setGenero(toGenero(v) ?? "")}
          >
            <SelectTrigger className="w-full bg-white">
              <SelectValue placeholder="Selecciona" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="V">Masculino</SelectItem>
              <SelectItem value="M">Femenino</SelectItem>
            </SelectContent>
          </Select>
        </LabeledField>

        <LabeledField label="Teléfono" error={errors.telefono}>
          <Input
            className="w-full bg-white"
            value={telefono}
            onChange={(e) =>
              setTelefono(stripNonDigits(e.target.value).slice(0, 9))
            }
            inputMode="numeric"
            maxLength={9}
            placeholder="Opcional"
          />
        </LabeledField>

        <LabeledField label="Talla" error={errors.shirtSize}>
          <Select
            value={shirtSize}
            onValueChange={(v) => setShirtSize(toTalla(v) ?? "M")}
          >
            <SelectTrigger className="w-full bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TALLAS.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </LabeledField>

        <LabeledField label="Rol" error={errors.rolDisciplina}>
          <Select
            value={rolDisciplina}
            onValueChange={(v) => setRolDisciplina(toRol(v))}
          >
            <SelectTrigger className="w-full bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((r) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </LabeledField>

        <LabeledField label="Acreditación" error={errors.acreditacion}>
          <Select
            value={acreditacion}
            onValueChange={(v) => setAcreditacion(toAcreditacion(v))}
          >
            <SelectTrigger className="w-full bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACREDITACIONES.map((a) => (
                <SelectItem key={a} value={a}>
                  {a}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </LabeledField>
      </div>

      <Button
        type="button"
        onClick={handleSubmit}
        className="btn-brand-gradient mt-4 w-full"
      >
        <Plus className="mr-2 size-4" />
        Agregar a la nómina
      </Button>
    </div>
  );
}

// ─── Main Modal ──────────────────────────────────────────────────────────────

export function InscripcionEditModal({
  open,
  onOpenChange,
  inscripcion,
  onSuccess,
}: InscripcionEditModalProps) {
  const updateMutation = useUpdateInscripcion();

  const equipoById = useMemo(
    () => Object.fromEntries(inscripcion.equipos.map((e) => [e.id, e])),
    [inscripcion.equipos],
  );

  const [catalogDisciplinas, setCatalogDisciplinas] = useState<
    DisciplinaOption[]
  >([]);

  // Discipline tabs come from the inscription's equipos immediately,
  // enriched with catalog names when available.
  const disciplinaOptions = useMemo<DisciplinaOption[]>(() => {
    const map = new Map<string, string>();
    for (const equipo of inscripcion.equipos) {
      map.set(equipo.disciplinaId, equipo.disciplinaNombre);
    }
    for (const disc of catalogDisciplinas) {
      map.set(disc.id, disc.nombre);
    }
    return [...map.entries()].map(([id, nombre]) => ({ id, nombre }));
  }, [inscripcion.equipos, catalogDisciplinas]);

  const disciplineMap = useMemo(
    () => Object.fromEntries(disciplinaOptions.map((d) => [d.id, d.nombre])),
    [disciplinaOptions],
  );

  const [teamName, setTeamName] = useState(
    inscripcion.inscripcion.teamName ?? "",
  );

  const [deportistas, setDeportistas] = useState<DeportistaEditData[]>(() => {
    const fallbackDisciplinaId = inscripcion.equipos[0]?.disciplinaId ?? null;
    return inscripcion.deportistas.map((d) => {
      const mapped = d.equipoIds
        .map((equipoId) => equipoById[equipoId]?.disciplinaId)
        .filter((id): id is string => Boolean(id));
      return {
        tipoDocumento: toTipoDocumento(d.persona.tipoDocumento),
        numeroDocumento: d.persona.numeroDocumento,
        nombres: d.persona.nombres,
        apellidos: d.persona.apellidos,
        genero: toGenero(d.persona.genero),
        telefono: d.persona.telefono,
        rolDisciplina: toRol(d.rolDisciplina),
        acreditacion: toAcreditacion(d.acreditacion),
        // Fall back to the inscription's first discipline if the link is missing,
        // so a player is never left without a discipline.
        disciplinaIds:
          mapped.length > 0
            ? mapped
            : fallbackDisciplinaId
              ? [fallbackDisciplinaId]
              : [],
        shirtSize: toTalla(d.shirtSize),
        id: d.id,
      };
    });
  });

  // Start with a valid discipline so the add form works immediately.
  const [activeDisc, setActiveDisc] = useState<string | null>(
    () => inscripcion.equipos[0]?.disciplinaId ?? null,
  );
  const [addErrors, setAddErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!open) return;
    getDisciplinas()
      .then((res) => {
        if (res.success && res.data) setCatalogDisciplinas(res.data);
      })
      .catch(() => {
        // Catalog is optional; tabs already come from the inscription.
      });
  }, [open]);

  // Keep activeDisc valid against the available disciplines.
  useEffect(() => {
    setActiveDisc((prev) => {
      if (prev && disciplinaOptions.some((d) => d.id === prev)) return prev;
      return disciplinaOptions[0]?.id ?? null;
    });
  }, [disciplinaOptions]);

  const activeDiscName = activeDisc
    ? (disciplineMap[activeDisc] ?? activeDisc)
    : "";

  const handleAddPlayer = useCallback(
    (payload: AddPlayerPayload): boolean => {
      setAddErrors({});

      if (!activeDisc) {
        setAddErrors({ disciplinaIds: "Selecciona una disciplina" });
        notify.error("Selecciona una disciplina antes de añadir");
        return false;
      }

      const parseResult = DeportistaEditSchema.safeParse({
        ...payload,
        disciplinaIds: [activeDisc],
      });

      if (!parseResult.success) {
        const schemaErrors: Record<string, string> = {};
        for (const issue of parseResult.error.issues) {
          const field = issue.path[0] as string;
          if (!schemaErrors[field]) schemaErrors[field] = issue.message;
        }
        setAddErrors(schemaErrors);
        notify.error("Revisa los campos marcados en rojo");
        return false;
      }

      const newPlayer = parseResult.data;

      const duplicateInDiscipline = deportistas.some(
        (d) =>
          d.numeroDocumento === newPlayer.numeroDocumento &&
          d.disciplinaIds.includes(activeDisc),
      );
      if (duplicateInDiscipline) {
        notify.error("Este deportista ya existe en esta disciplina");
        return false;
      }

      const existingDocIdx = deportistas.findIndex(
        (d) => d.numeroDocumento === newPlayer.numeroDocumento,
      );

      if (existingDocIdx >= 0) {
        setDeportistas((prev) =>
          prev.map((d, idx) =>
            idx === existingDocIdx
              ? { ...d, disciplinaIds: [...d.disciplinaIds, activeDisc] }
              : d,
          ),
        );
        notify.success("Deportista agregado a esta disciplina");
      } else {
        setDeportistas((prev) => [...prev, newPlayer]);
        notify.success("Deportista agregado a la nómina");
      }

      setAddErrors({});
      return true;
    },
    [activeDisc, deportistas],
  );

  const handleRemovePlayer = useCallback((docNum: string, discId: string) => {
    setDeportistas((prev) =>
      prev
        .map((d) => {
          if (d.numeroDocumento === docNum) {
            return {
              ...d,
              disciplinaIds: d.disciplinaIds.filter((id) => id !== discId),
            };
          }
          return d;
        })
        .filter((d) => d.disciplinaIds.length > 0),
    );
  }, []);

  const handleSave = useCallback(async () => {
    const trimmedTeamName = (teamName ?? "").trim();
    if (!trimmedTeamName) {
      notify.error("El nombre del equipo es requerido");
      return;
    }
    if (deportistas.length === 0) {
      notify.error("Debe haber al menos un deportista");
      return;
    }
    if (deportistas.some((d) => d.disciplinaIds.length === 0)) {
      notify.error("Hay deportistas sin disciplina asignada");
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: inscripcion.inscripcion.id,
        payload: {
          teamName: trimmedTeamName,
          deportistas: deportistas.map((d) => ({
            tipoDocumento: d.tipoDocumento,
            numeroDocumento: d.numeroDocumento,
            nombres: d.nombres,
            apellidos: d.apellidos,
            genero: d.genero,
            telefono: d.telefono,
            rolDisciplina: d.rolDisciplina,
            acreditacion: d.acreditacion,
            disciplinaIds: d.disciplinaIds,
            shirtSize: d.shirtSize,
          })),
        },
      });
      notify.success("Inscripción actualizada correctamente");
      onSuccess?.();
      onOpenChange(false);
    } catch {
      // Error is handled by the mutation.
    }
  }, [
    teamName,
    deportistas,
    inscripcion.inscripcion.id,
    updateMutation,
    onSuccess,
    onOpenChange,
  ]);

  const handleClose = () => {
    if (updateMutation.isPending) return;
    onOpenChange(false);
  };

  return (
    <GenericModal
      open={open}
      onOpenChange={handleClose}
      preventClose={updateMutation.isPending}
    >
      <GenericModal.Content size="lg">
        <GenericModal.Header
          title=""
          className="border-b border-border bg-primary/[0.03] px-4 py-4 sm:px-6 sm:py-5"
        >
          <div className="flex w-full items-center gap-3">
            <div className="shrink-0 rounded-xl border border-primary/20 bg-primary/10 p-2 shadow-sm">
              <Pencil className="h-5 w-5 text-primary" />
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-0.5">
              <span className="hidden text-[10px] font-bold uppercase leading-none tracking-widest text-primary sm:block">
                Salesianos FEST 2026
              </span>
              <h2 className="text-xl font-black leading-tight tracking-tight text-foreground sm:text-2xl">
                Editar Inscripción
              </h2>
              <p className="hidden text-sm leading-relaxed text-muted-foreground sm:block">
                Modifica el nombre del equipo y la nómina de deportistas
              </p>
            </div>
          </div>
        </GenericModal.Header>

        <GenericModal.Body className="min-h-0 px-3 sm:px-6">
          <div className="flex w-full flex-col gap-5">
            <EditTeamNameField value={teamName} onChange={setTeamName} />

            <DisciplineTabs
              disciplinas={disciplinaOptions}
              activeDisc={activeDisc}
              onSelect={setActiveDisc}
            />

            <div className="space-y-3">
              <Label className="text-xs font-bold uppercase text-muted-foreground">
                Nómina actual
              </Label>
              <CurrentRosterList
                deportistas={deportistas}
                activeDisc={activeDisc}
                onRemove={handleRemovePlayer}
              />
            </div>

            <AddDeportistaPanel
              activeDisc={activeDisc}
              activeDiscName={activeDiscName}
              onAdd={handleAddPlayer}
              errors={addErrors}
            />
          </div>
        </GenericModal.Body>

        <GenericModal.Footer className="flex flex-col-reverse gap-2 border-t border-border bg-muted/30 px-4 py-4 sm:flex-row sm:justify-end sm:gap-2 sm:px-6">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={updateMutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending}
            className="btn-brand-gradient"
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Guardando...
              </>
            ) : (
              "Guardar cambios"
            )}
          </Button>
        </GenericModal.Footer>

        <GenericModal.CloseX />
      </GenericModal.Content>
    </GenericModal>
  );
}
