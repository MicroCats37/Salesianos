"use client";

import { Layers, Users } from "lucide-react";
import { useController, useFormContext } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AltaInscripcionFormData } from "../schemas/alta-inscripcion.schema";
import type {
  CategoriaCatalogo,
  PromocionCatalogo,
} from "../types/inscripcion.types";

export interface PasoPromocionProps {
  /** The cohorts of the edition, as the catalogue publishes them. */
  promociones: readonly PromocionCatalogo[];
  /** The competitive bands of the edition, as the catalogue publishes them. */
  categorias: readonly CategoriaCatalogo[];
}

/**
 * PasoPromocion - the cohort of the registration.
 *
 * The visitor selects the cohort that he/she belongs to. It is an EXPLICIT
 * selection, because the cohort is the only input from which the server
 * derives the competitive band of the teams.
 *
 * ## What the browser NEVER does here
 *
 * It NEVER resolves which band the chosen cohort belongs to. The bands are
 * printed with the range of cohorts that they DECLARE, and the resolution is
 * the server's (`RN-C02`, `QA-K01`). A preview that "guessed" the band would
 * be a rule of the browser in the place where the server owns it.
 *
 * ## The secondary cohort
 *
 * The secondary cohort of a fused registration is OPTIONAL and DESCRIPTIVE:
 * it names the visible label of a fused cohort and it never changes the
 * band, the cupos, the payment, the team or the eligibility. The step says
 * so, in the words of the domain.
 *
 * The step reads only the fields it owns with `useController`: it never
 * watches the whole form (contract/smart.md 5.2).
 */
export function PasoPromocion(props: PasoPromocionProps) {
  const promociones = props.promociones;
  const categorias = props.categorias;

  const contexto = useFormContext<AltaInscripcionFormData>();

  /**
   * The two cohorts of the step.
   *
   * They are CONTROLLED fields (they are `Select`s, not `Input`s), so they
   * need `useController`: the value, the change, the blur and the error of
   * each one come from the controller, and the label and the error are drawn
   * ONCE, by `FormField`.
   */
  const { field: promocion, fieldState: estadoPromocion } = useController({
    control: contexto.control,
    name: "promocion_id",
  });

  const { field: fusion, fieldState: estadoFusion } = useController({
    control: contexto.control,
    name: "fusion_promocion_id",
  });

  return (
    <fieldset className="flex flex-col gap-4">
      <legend className="text-sm font-semibold text-foreground">
        La promoción a la que perteneces
      </legend>

      <p className="text-caption text-muted-foreground">
        La promoción es el año de tu cohorte. El comité lo usa para asignar la
        categoría deportiva de cada equipo, y lo decide el servidor: aquí sólo
        eliges tu año.
      </p>

      <FormGrid>
        <FormField
          id="alta-promocion"
          label="Tu promoción"
          required
          icon={Users}
          span={6}
          error={estadoPromocion.error?.message}
        >
          {(control) => (
            <Select
              value={promocion.value || undefined}
              onValueChange={(valor) => promocion.onChange(valor)}
            >
              <SelectTrigger
                {...control}
                onBlur={promocion.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige tu promoción" />
              </SelectTrigger>
              <SelectContent>
                {promociones.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.nombre} · {item.anio}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id="alta-fusion-promocion"
          label="Promoción fusionada (opcional)"
          icon={Layers}
          span={6}
          helper="La promoción fusionada es un dato descriptivo: nombra la etiqueta visible de una promoción fusionada y no cambia la categoría, los cupos, el pago ni la elegibilidad."
          error={estadoFusion.error?.message}
        >
          {(control) => (
            <Select
              value={fusion.value ?? undefined}
              onValueChange={(valor) => fusion.onChange(valor)}
            >
              <SelectTrigger
                {...control}
                onBlur={fusion.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Sin fusión" />
              </SelectTrigger>
              <SelectContent>
                {promociones.map((item) => (
                  <SelectItem
                    key={item.id}
                    value={item.id}
                    disabled={item.id === promocion.value}
                  >
                    {item.nombre} · {item.anio}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </FormField>
      </FormGrid>

      {categorias.length > 0 ? (
        <div className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4">
          <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Users
              className="size-4 text-muted-foreground"
              aria-hidden="true"
            />
            Categorías de esta edición
          </span>
          <ul className="flex flex-col gap-1">
            {categorias.map((categoria) => (
              <li
                key={categoria.id}
                className="flex flex-wrap items-baseline gap-x-2 text-caption text-muted-foreground"
              >
                <span className="font-semibold text-foreground">
                  {categoria.nombre}
                </span>
                <span className="tabular-nums">
                  Promociones {categoria.promocion_desde}–
                  {categoria.promocion_hasta}
                </span>
              </li>
            ))}
          </ul>
          <p className="text-caption text-muted-foreground">
            La categoría de cada equipo la resuelve el servidor con tu
            promoción: esta lista es sólo la referencia de las categorías de la
            edición.
          </p>
        </div>
      ) : null}
    </fieldset>
  );
}
