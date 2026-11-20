"use client";

import { AlertCircle, Plus, Trash2 } from "lucide-react";
import { useFormContext, useWatch } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

function erroresDeEquipo(
  errores: Record<string, unknown>,
): ErroresEquipo[] {
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

  function agregarEquipo() {
    setValue(
      "equipos",
      [...equipos, { disciplina_id: "", nombre: "" }],
      { shouldDirty: true },
    );
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
          const idDisciplina = "equipo-" + indice + "-disciplina";
          const idNombre = "equipo-" + indice + "-nombre";
          const idErrorDisciplina = idDisciplina + "-error";
          const idErrorNombre = idNombre + "-error";

          const errorDisciplina = erroresEquipo[indice]?.disciplina_id
            ?.message;
          const errorNombre = erroresEquipo[indice]?.nombre?.message;

          const campoDisciplina = ("equipos." + indice + ".disciplina_id") as CampoEquipo;
          const campoNombre = ("equipos." + indice + ".nombre") as CampoEquipo;

          const registroDisciplina = registro(campoDisciplina);
          const registroNombre = registro(campoNombre);

          return (
            <div
              key={indice}
              className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-foreground">
                  Equipo {indice + 1}
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

              <div className="flex flex-col gap-1.5">
                <Label
                  htmlFor={idDisciplina}
                  className="text-sm font-semibold text-foreground"
                >
                  Disciplina
                </Label>
                <select
                  id={idDisciplina}
                  name={registroDisciplina.name}
                  onChange={registroDisciplina.onChange}
                  onBlur={registroDisciplina.onBlur}
                  ref={registroDisciplina.ref}
                  aria-invalid={Boolean(errorDisciplina)}
                  aria-describedby={
                    errorDisciplina ? idErrorDisciplina : undefined
                  }
                  className="min-h-11 w-full rounded-[var(--radius-md)] border border-input bg-transparent px-3 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/20"
                >
                  <option value="">Elige la disciplina</option>
                  {disciplinas.map((disciplina) => (
                    <option key={disciplina.id} value={disciplina.id}>
                      {disciplina.nombre}
                    </option>
                  ))}
                </select>
                {errorDisciplina ? (
                  <p
                    id={idErrorDisciplina}
                    className="flex items-center gap-1.5 text-xs text-destructive"
                  >
                    <AlertCircle
                      className="size-3.5 shrink-0"
                      aria-hidden="true"
                    />
                    {errorDisciplina}
                  </p>
                ) : null}
              </div>

              <div className="flex flex-col gap-1.5">
                <Label
                  htmlFor={idNombre}
                  className="text-sm font-semibold text-foreground"
                >
                  Nombre del equipo
                </Label>
                <Input
                  id={idNombre}
                  type="text"
                  name={registroNombre.name}
                  onChange={registroNombre.onChange}
                  onBlur={registroNombre.onBlur}
                  ref={registroNombre.ref}
                  autoComplete="off"
                  placeholder="Por ejemplo, Halcones"
                  aria-invalid={Boolean(errorNombre)}
                  aria-describedby={errorNombre ? idErrorNombre : undefined}
                  className="min-h-11"
                />
                {errorNombre ? (
                  <p
                    id={idErrorNombre}
                    className="flex items-center gap-1.5 text-xs text-destructive"
                  >
                    <AlertCircle
                      className="size-3.5 shrink-0"
                      aria-hidden="true"
                    />
                    {errorNombre}
                  </p>
                ) : null}
              </div>
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
