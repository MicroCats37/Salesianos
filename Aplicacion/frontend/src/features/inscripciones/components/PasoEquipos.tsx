"use client";

import { AlertCircle, Plus, Tag, Trash2, Trophy } from "lucide-react";
import { useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchableSelect } from "@/components/ui/searchable-select";
import type { AltaInscripcionFormData } from "../schemas/alta-inscripcion.schema";
import type { DisciplinaCatalogo } from "../types/inscripcion.types";

export interface PasoEquiposProps {
  /** The disciplines that the chosen package opens. */
  disciplinas: readonly DisciplinaCatalogo[];
}

/** The path of a field of a team, as React Hook Form expects it. */
type CampoEquipo =
  | `equipos.${number}.disciplina_id`
  | `equipos.${number}.nombre`;

/** The errors of the array of teams, read without inventing a shape. */
interface ErroresEquipo {
  message?: string;
  disciplina_id?: { message?: string };
  nombre?: { message?: string };
}

function erroresDeEquipo(errores: Record<string, unknown>): ErroresEquipo[] {
  const lista = errores.equipos;
  if (!Array.isArray(lista)) return [];
  return lista as unknown as ErroresEquipo[];
}

function mensajeDeLista(errores: Record<string, unknown>): string | undefined {
  const lista = errores.equipos;
  if (!lista || typeof lista !== "object" || Array.isArray(lista)) {
    return undefined;
  }
  const mensaje = (lista as { message?: string }).message;
  return typeof mensaje === "string" ? mensaje : undefined;
}

/**
 * PasoEquipos - the second step of the wizard.
 *
 * The visitor declares the teams of the registration: the discipline and
 * the name of each one. The list grows and shrinks with the visitor, and
 * the server decides how many teams a registration may declare.
 *
 * The disciplines are the ones the chosen package opens. They are published
 * by the catalogue, so the option list is a READ of the catalogue and never
 * a rule of the browser.
 *
 * The step reads only the field it owns with `useWatch`: it never watches
 * the whole form (contract/smart.md 5.2).
 */
export function PasoEquipos(props: PasoEquiposProps) {
  const disciplinas = props.disciplinas;

  const contexto = useFormContext<AltaInscripcionFormData>();
  const registro = contexto.register;
  const setValue = contexto.setValue;
  const errores = contexto.formState.errors;

  const observacionEquipos = {
    control: contexto.control,
    name: "equipos" as const,
  };
  const equipos = useWatch(observacionEquipos) ?? [];

  const erroresEquipo = erroresDeEquipo(errores);
  const errorLista = mensajeDeLista(errores);

  /**
   * The disciplines are PRE-FILLED.
   *
   * It is COPIED from the previous frontend
   * (`frontend/src/features/inscripciones/components/smart-fields/
   * SmartEquipoField.tsx`): the package opens a set of disciplines and the
   * slots that the visitor has not touched yet take them, one by one and
   * without repeating. The visitor arrives at the step with the sports
   * already chosen and only has to name the teams.
   *
   * It is idempotent on purpose: the rows of the form and the data of the
   * catalogue can arrive in different renders, and a one-shot guard would
   * leave the last rows empty.
   */
  useEffect(() => {
    if (disciplinas.length === 0) return;
    if (equipos.length === 0) return;

    const usadas = new Set(
      equipos.map((equipo) => equipo.disciplina_id).filter(Boolean),
    );

    let cursor = 0;

    const siguiente = equipos.map((equipo) => {
      if (equipo.disciplina_id) return equipo;

      while (
        cursor < disciplinas.length &&
        usadas.has(disciplinas[cursor].id)
      ) {
        cursor += 1;
      }

      const encontrada = disciplinas[cursor];
      if (!encontrada) return equipo;

      usadas.add(encontrada.id);
      cursor += 1;

      return { ...equipo, disciplina_id: encontrada.id };
    });

    const cambio = siguiente.some(
      (equipo, indice) =>
        equipo.disciplina_id !== (equipos[indice]?.disciplina_id ?? ""),
    );

    if (cambio) {
      setValue("equipos", siguiente, { shouldDirty: true });
    }
  }, [disciplinas, equipos, setValue]);

  function agregarEquipo() {
    setValue("equipos", [...equipos, { disciplina_id: "", nombre: "" }], {
      shouldDirty: true,
    });
  }

  function quitarEquipo(indice: number) {
    setValue(
      "equipos",
      equipos.filter((_, posicion) => posicion !== indice),
      { shouldDirty: true },
    );
  }

  return (
    <fieldset className="flex flex-col gap-4">
      <legend className="text-sm font-semibold text-foreground">
        Los equipos que se anotan
      </legend>

      <p className="text-caption text-muted-foreground">
        Cada equipo indica la disciplina en la que compite y el nombre con el
        que aparece en la lista. El comité valida la nómina después.
      </p>

      <div className="flex flex-col gap-3">
        {equipos.map((equipo, indice) => {
          const idDisciplina = `equipo-${indice}-disciplina`;
          const idNombre = `equipo-${indice}-nombre`;

          const errorDisciplina = erroresEquipo[indice]?.disciplina_id?.message;
          const errorNombre = erroresEquipo[indice]?.nombre?.message;

          const campoDisciplina =
            `equipos.${indice}.disciplina_id` as CampoEquipo;
          const campoNombre = `equipos.${indice}.nombre` as CampoEquipo;

          const registroNombre = registro(campoNombre);

          return (
            <div
              key={indice}
              className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 transition-colors duration-(--motion-duration-fast) hover:border-border-strong"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {indice + 1}
                  </span>
                  <span className="text-sm font-semibold text-foreground">
                    Equipo {indice + 1}
                  </span>
                </span>

                {equipos.length > 1 ? (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => quitarEquipo(indice)}
                    className="min-h-11 px-3 text-destructive"
                  >
                    <Trash2 className="size-4" aria-hidden="true" />
                    Quitar
                  </Button>
                ) : null}
              </div>

              <FormGrid>
                <FormField
                  id={idDisciplina}
                  label="Disciplina"
                  required
                  icon={Trophy}
                  span={6}
                  error={errorDisciplina}
                >
                  {() => (
                    /*
                     * The searchable select of the project, as the previous
                     * frontend had it: the discipline list grows and the
                     * keyboard reaches it. The ICON belongs to the field
                     * (`FormField`), so the control draws it once.
                     */
                    <SearchableSelect
                      id={idDisciplina}
                      label="Disciplina"
                      value={equipo?.disciplina_id || null}
                      onValueChange={(valor) =>
                        setValue(campoDisciplina, valor ?? "", {
                          shouldDirty: true,
                        })
                      }
                      options={disciplinas.map((disciplina) => ({
                        value: disciplina.id,
                        label: disciplina.nombre,
                      }))}
                      placeholder="Elige la disciplina"
                      error={Boolean(errorDisciplina)}
                      errorMessage={errorDisciplina}
                      showLabel={false}
                      hideErrorMessage
                      className="w-full [&_button]:w-full"
                    />
                  )}
                </FormField>

                <FormField
                  id={idNombre}
                  label="Nombre del equipo"
                  required
                  icon={Tag}
                  span={6}
                  error={errorNombre}
                >
                  {(control) => (
                    <Input
                      {...control}
                      type="text"
                      name={registroNombre.name}
                      onChange={registroNombre.onChange}
                      onBlur={registroNombre.onBlur}
                      ref={registroNombre.ref}
                      autoComplete="off"
                      placeholder="Por ejemplo, Halcones"
                    />
                  )}
                </FormField>
              </FormGrid>
            </div>
          );
        })}
      </div>

      {errorLista ? (
        <p
          role="alert"
          className="flex items-center gap-1.5 text-sm text-destructive"
        >
          <AlertCircle className="size-4 shrink-0" aria-hidden="true" />
          {errorLista}
        </p>
      ) : null}

      <Button
        type="button"
        variant="outline"
        onClick={agregarEquipo}
        className="min-h-11 self-start"
      >
        <Plus className="size-4" aria-hidden="true" />
        Agregar un equipo
      </Button>
    </fieldset>
  );
}
