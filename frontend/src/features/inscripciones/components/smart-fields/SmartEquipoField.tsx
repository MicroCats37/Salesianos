"use client";

// SmartEquipoField — manages an array of equipos for one inscription.
// - Disciplinas limited to paquete_disciplinas
// - Auto-creates N equipos based on paquete.cantidad_disciplinas_requeridas
// - One equipo per disciplina (no duplicates)
// - Categoria is null for now (backend already accepts null)
// - Layout responsive: desktop 2-col grid; mobile vertical stack

import { gsap } from "gsap";
import { Lock, User } from "lucide-react";
import { useEffect, useRef } from "react";
import { Controller, useFieldArray, useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SearchableSelect } from "@/components/ui/searchable-select";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn, stripNonDigits } from "@/lib/utils";
import type { InscripcionFormData } from "../../schemas/inscripcion.schema";
import type { PaqueteDisciplina } from "../../services/catalog.service";

// Participant entry has been removed from the creation wizard.
// Participants are added from the inscription detail view after creation.
// The AddParticipanteSidePanel is used for that purpose (imported in InscripcionDetailView).

// ── Equipo Card ──────────────────────────────────────────────────────────────

interface EquipoCardProps {
  index: number;
  paqueteId: string;
  paqueteDisciplinas:
    | PaqueteDisciplina[]
    | undefined;
  locked: boolean;
  permiteDuplicados: boolean;
}


function EquipoCard({
  index,
  paqueteId,
  paqueteDisciplinas,
  locked,
}: EquipoCardProps) {
  const {
    control,
    watch,
    formState: { errors },
  } = useFormContext<InscripcionFormData>();
  // Always offer the full package catalogue in every card so the user can
  // switch disciplines freely. Backend validation enforces capacity and
  // duplicate rules; we do not hide options client-side.
  const opcionesCatalogo = (paqueteDisciplinas ?? []).map((d) => ({
    value: d.disciplina_id,
    label: `${d.disciplina_nombre} (${d.disciplina_sigla})`,
  }));

  const equiposErrors =
    (errors.equipos as unknown as
      | Array<{
          disciplina_id?: { message?: string };
          nombre?: { message?: string };
        }>
      | undefined) ?? [];
  const equipoError = equiposErrors[index];
  const disciplinaError = equipoError?.disciplina_id?.message;
  const nombreError = equipoError?.nombre?.message;

  const cardRef = useRef<HTMLDivElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-animate on team index change.
  useEffect(() => {
    const card = cardRef.current;
    if (!card) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        card,
        { y: 16, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.45, ease: "power3.out" },
      );
    }, card);
    return () => ctx.revert();
  }, [index]);

  return (
    <div
      ref={cardRef}
      className="rounded-2xl bg-white border border-slate-200 shadow-sm p-4 space-y-4"
    >
      <div className="flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-600 text-white text-sm font-bold shadow-sm">
          {index + 1}
        </div>
        <h4 className="font-bold text-slate-900">Equipo {index + 1}</h4>
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
          Disciplina {locked && <span className="text-emerald-600">(bloqueado)</span>} <span className="text-amber-600">*</span>
        </Label>
        {locked ? (
          <Controller
            name={`equipos.${index}.disciplina_id`}
            control={control}
            render={({ field }) => {
              const selectedDisciplina = (paqueteDisciplinas ?? []).find(
                (d) => d.disciplina_id === field.value,
              );
              return (
                <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
                  <Lock className="size-4 text-slate-400 shrink-0" />
                  <span className="text-sm font-medium text-slate-700">
                    {selectedDisciplina
                      ? `${selectedDisciplina.disciplina_nombre} (${selectedDisciplina.disciplina_sigla})`
                      : "Sin disciplina asignada"}
                  </span>
                </div>
              );
            }}
          />
        ) : (
          <Controller
            name={`equipos.${index}.disciplina_id`}
            control={control}
            render={({ field }) => (
              <SearchableSelect
                id={`equipos.${index}.disciplina_id`}
                label="Disciplina"
                value={field.value || null}
                onValueChange={(value) => field.onChange(value)}
                options={opcionesCatalogo}
                placeholder={
                  paqueteId ? "Busca una disciplina" : "Selecciona un paquete"
                }
                disabled={!paqueteId}
                error={!!disciplinaError}
                errorMessage={disciplinaError}
                showLabel={false}
                hideErrorMessage
                className="w-full [&_button]:w-full"
              />
            )}
          />
        )}
        {disciplinaError && (
          <p className="text-xs text-red-600">{disciplinaError}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
          Nombre del equipo <span className="text-amber-600">*</span>
        </Label>
        <Controller
          name={`equipos.${index}.nombre`}
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              type="text"
              placeholder="Los Tigres FC"
              className="bg-white border-slate-300"
            />
          )}
        />
        {nombreError && <p className="text-xs text-red-600">{nombreError}</p>}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Participantes
          </Label>
          <span className="text-xs font-semibold text-slate-400">
            0
          </span>
        </div>
        <div className="rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 p-4 text-center">
          <User className="size-6 text-slate-300 mx-auto mb-1" />
          <p className="text-xs text-slate-500">
            Los participantes se agregan desde el detalle de la inscripción, después de crearla.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Smart Equipo Field (public) ───────────────────────────────────────────────

interface SmartEquipoFieldProps {
  fieldName: "equipos";
  paqueteIdFieldName: "paquete_id";
  paqueteActual?: {
    id: string;
    cantidad_disciplinas_requeridas: number;
    cantidad_maxima_equipos: number;
    cantidad_maxima_participantes: number;
    modo_disciplinas: string;
    disciplinas: PaqueteDisciplina[];
  };
}

export function SmartEquipoField({
  fieldName,
  paqueteIdFieldName,
  paqueteActual,
}: SmartEquipoFieldProps) {
  const { control, watch, getValues } = useFormContext<InscripcionFormData>();
  const paqueteId = watch(paqueteIdFieldName);
  const paqueteDisciplinas = paqueteActual?.disciplinas ?? [];

  const { fields: equipos, replace } = useFieldArray({
    control,
    name: fieldName,
  });
  const equiposActuales =
    (watch(fieldName) as unknown as Array<{
      disciplina_id?: string;
      categoria_id: string | null;
      nombre: string;
    }>) ?? [];

  // Allow duplicate discipline selection when package has more team slots than distinct
  // disciplines available (i.e., the user has room to pick the same discipline twice).
  const permiteDuplicados =
    (paqueteActual?.cantidad_maxima_equipos ?? 1) >
    (paqueteDisciplinas?.length ?? 0);

  const containerRef = useRef<HTMLDivElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-animate team list on count change.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".equipo-card",
        { y: 16, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, stagger: 0.08, ease: "power3.out" },
      );
    }, container);
    return () => ctx.revert();
  }, [equipos.length]);

  // Auto-create equipos when paquete changes. The wizard NEVER exposes
  // "Agregar/Quitar equipo" controls — `cantidad_maxima_equipos` is the
  // single source of truth from the backend presenter.
  const lastPaqueteIdRef = useRef<string | null>(null);
  const lastTargetCountRef = useRef<number | null>(null);
  // biome-ignore lint/correctness/useExhaustiveDependencies: sync equipos when paquete changes.
  useEffect(() => {
    if (!paqueteActual || !paqueteActual.id) {
      lastPaqueteIdRef.current = paqueteId || null;
      return;
    }

    const targetCount = Math.max(paqueteActual.cantidad_maxima_equipos ?? 1, 1);
    const currentEquipos = getValues(fieldName) ?? [];

    // Reset buffer whenever the package selection changes.
    if (lastPaqueteIdRef.current !== paqueteActual.id) {
      lastPaqueteIdRef.current = paqueteActual.id;
      lastTargetCountRef.current = targetCount;
      if (currentEquipos.length !== targetCount) {
        const preserved = currentEquipos.slice(0, targetCount);
        const next = Array.from({ length: targetCount }, (_, i) => {
          const prev = preserved[i];
          return (
            prev ?? {
              disciplina_id: "",
              categoria_id: null,
              nombre: "",
              participantes: [],
            }
          );
        });
        replace(next);
      }
      return;
    }

    // Same package id, but cap may have changed (catalog reloaded). Sync slots.
    if (lastTargetCountRef.current !== targetCount) {
      lastTargetCountRef.current = targetCount;
      if (currentEquipos.length !== targetCount) {
        const preserved = currentEquipos.slice(0, targetCount);
        const next = Array.from({ length: targetCount }, (_, i) => {
          const prev = preserved[i];
          return (
            prev ?? {
              disciplina_id: "",
              categoria_id: null,
              nombre: "",
              participantes: [],
            }
          );
        });
        replace(next);
      }
    }
  }, [paqueteActual?.id, paqueteActual?.cantidad_maxima_equipos]);

  // Compute error state for FIJO mode misconfiguration
  const isFIJO = paqueteActual?.modo_disciplinas === "FIJO";
  const hasError =
    isFIJO &&
    paqueteDisciplinas != null &&
    paqueteDisciplinas.length > 0 &&
    paqueteDisciplinas.length !== (paqueteActual?.cantidad_disciplinas_requeridas ?? 1);

  const errorMessage =
    isFIJO && paqueteDisciplinas?.length === 0
      ? "Este paquete no tiene disciplinas configuradas"
      : isFIJO && hasError
        ? `Configuración inválida: el paquete permite ${paqueteDisciplinas?.length} disciplinas pero requiere ${paqueteActual?.cantidad_disciplinas_requeridas}`
        : !isFIJO &&
          paqueteDisciplinas != null &&
          paqueteDisciplinas.length < (paqueteActual?.cantidad_disciplinas_requeridas ?? 1)
          ? `Este paquete permite ${paqueteDisciplinas?.length} disciplinas pero requiere ${paqueteActual?.cantidad_disciplinas_requeridas}`
          : null;

  // Auto-fill disciplines whenever the package can determine every slot.
  // This is intentionally idempotent: field-array rows and catalog data can
  // arrive in different renders, so a one-shot guard can leave later rows empty.
  // biome-ignore lint/correctness/useExhaustiveDependencies: depends on watched equipos through equiposActuales.
  useEffect(() => {
    if (
      !paqueteDisciplinas ||
      paqueteDisciplinas.length === 0 ||
      !paqueteActual
    ) {
      return;
    }
    if (paqueteActual.id !== lastPaqueteIdRef.current) return;

    const modo = paqueteActual.modo_disciplinas;
    const required = paqueteActual.cantidad_disciplinas_requeridas ?? 1;
    const disponibles = paqueteDisciplinas.length;

    const targetCount = Math.max(paqueteActual.cantidad_maxima_equipos ?? required, 1);
    const currentEquipos = getValues(fieldName) ?? [];
    const baseEquipos = Array.from({ length: targetCount }, (_, i) => {
      const prev = currentEquipos[i];
      return (
        prev ?? {
          disciplina_id: "",
          categoria_id: null,
          nombre: "",
          participantes: [],
        }
      );
    });

    const disciplinaIds = paqueteDisciplinas.map((d) => d.disciplina_id);
    const currentIds = baseEquipos.map((eq) => eq.disciplina_id).filter(Boolean);
    const allCurrentIdsBelongToPackage = currentIds.every((id) =>
      disciplinaIds.includes(id),
    );
    const hasDistinctCurrentIds = new Set(currentIds).size === currentIds.length;
    const hasCompleteValidSelection =
      currentIds.length === targetCount &&
      allCurrentIdsBelongToPackage &&
      hasDistinctCurrentIds;

    // Pre-fill rules:
    // - FIJO mode: always pre-fill every slot with the matching package
    //   discipline (locked, pre-fill is safe).
    // - ELEGIBLE mode: always pre-fill empty slots with the next available
    //   package discipline so the user sees a sensible starting point. Slots
    //   beyond the available disciplines remain empty and the user can
    //   duplicate any prior selection when paquete capacity allows it.
    const needsPrefill =
      modo === "FIJO"
        ? !hasCompleteValidSelection
        : baseEquipos.some((eq) => !eq.disciplina_id);
    if (needsPrefill) {
      const usados = new Set<string>(
        baseEquipos.map((eq) => eq.disciplina_id).filter(Boolean),
      );
      let cursor = 0;
      const next = baseEquipos.map((eq, i) => {
        if (eq.disciplina_id) return eq;
        while (
          cursor < paqueteDisciplinas.length &&
          usados.has(paqueteDisciplinas[cursor].disciplina_id)
        ) {
          cursor += 1;
        }
        const match = paqueteDisciplinas[cursor];
        if (match) {
          usados.add(match.disciplina_id);
          cursor += 1;
          return { ...eq, disciplina_id: match.disciplina_id };
        }
        return eq;
      });
      const previousSnapshot = currentEquipos.map((eq) => ({
        disciplina_id: eq.disciplina_id,
      }));
      const nextSnapshot = next.map((eq) => ({ disciplina_id: eq.disciplina_id }));
      const changed =
        previousSnapshot.length !== nextSnapshot.length ||
        previousSnapshot.some(
          (eq, i) => eq.disciplina_id !== nextSnapshot[i].disciplina_id,
        );
      if (changed) {
        replace(next);
      }
    }
  }, [paqueteDisciplinas, paqueteActual?.id, paqueteId, equipos.length, equiposActuales]);

  // Compute locked state per slot.
  // FIJO with available === required: all slots locked.
  // ELEGIBLE: no locking (user can rearrange).
  const isModoFIJOAndMatched =
    isFIJO &&
    paqueteDisciplinas != null &&
    paqueteDisciplinas.length > 0 &&
    paqueteDisciplinas.length === (paqueteActual?.cantidad_disciplinas_requeridas ?? 1) &&
    equiposActuales.length === paqueteDisciplinas.length &&
    equiposActuales.every((equipo) => Boolean(equipo.disciplina_id));

  return (
    <div ref={containerRef} className="space-y-4">
      <div className="flex items-start gap-3 rounded-xl bg-sky-50 border border-sky-200 p-3 text-xs text-slate-600">
        <User className="size-4 text-sky-600 shrink-0 mt-0.5" />
        <p>
          Tu paquete define cuántas disciplinas debes inscribir. Cada equipo
          corresponde a una disciplina
          {permiteDuplicados
            ? " — puedes seleccionar la misma disciplina para más de un equipo."
            : " — solo puedes elegir una disciplina distinta por equipo."}
        </p>
      </div>

      {errorMessage && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {errorMessage}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {equipos.map((field, index) => (
          <div key={field.id} className="equipo-card">
            <EquipoCard
              index={index}
              paqueteId={paqueteId}
              paqueteDisciplinas={paqueteDisciplinas}
              locked={isModoFIJOAndMatched}
              permiteDuplicados={permiteDuplicados}
            />
          </div>
        ))}
      </div>

      {!paqueteId && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 text-center">
          Selecciona un paquete en el paso anterior para crear tus equipos.
        </div>
      )}
    </div>
  );
}

void cn;
