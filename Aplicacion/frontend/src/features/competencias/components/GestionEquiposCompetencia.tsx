"use client";

import { Hash, ListOrdered, NotebookPen, ToggleRight } from "lucide-react";
import { useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import type { z } from "zod";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import {
  useEditarEquipo,
  useEquiposElegibles,
  useIncorporarEquipo,
} from "../hooks/useCompetencias";
import {
  type EquipoEditar,
  type EquipoIncorporar,
  equipoEditarSchema,
  equipoIncorporarSchema,
} from "../schemas/competencia.schema";
import type { CompetenciaEquipo } from "../types/competencia.types";

const equipoEditarFormSchema = equipoEditarSchema.omit({
  expected_version: true,
});
type EquipoEditarForm = z.infer<typeof equipoEditarFormSchema>;

/** Administra la selección y el orden manual antes de generar la llave. */
export function GestionEquiposCompetencia({
  competenciaId,
  equipos,
  bloqueado = false,
}: {
  competenciaId: string;
  equipos: CompetenciaEquipo[];
  bloqueado?: boolean;
}) {
  const [altaAbierta, setAltaAbierta] = useState(false);
  const [equipoEnEdicion, setEquipoEnEdicion] =
    useState<CompetenciaEquipo | null>(null);
  const elegibles = useEquiposElegibles(competenciaId);
  const incorporar = useIncorporarEquipo();
  const editar = useEditarEquipo();
  const opciones = (elegibles.data ?? [])
    .filter((equipo) => equipo.es_elegible)
    .map((equipo) => ({ value: equipo.equipo_id, label: equipo.nombre }));

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {bloqueado
            ? "El cuadro ya fue generado; el orden se conserva como historial operativo."
            : "Selecciona sólo equipos elegibles y define su orden antes de generar el cuadro."}
        </p>
        <Button
          type="button"
          onClick={() => setAltaAbierta(true)}
          disabled={bloqueado || elegibles.isPending}
        >
          Incorporar equipo
        </Button>
      </div>

      {equipos.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {equipos.map((equipo) => (
            <li
              key={equipo.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border px-3 py-2"
            >
              <span className="text-sm font-medium">
                {equipo.orden}. {equipo.equipo_nombre}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {equipo.estado}
                </span>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={bloqueado}
                  onClick={() => setEquipoEnEdicion(equipo)}
                >
                  Editar o retirar
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <AppFormModal<EquipoIncorporar>
        open={altaAbierta}
        onOpenChange={setAltaAbierta}
        title="Incorporar equipo elegible"
        eyebrow="Cuadro"
        description="El servidor vuelve a comprobar la elegibilidad al guardar."
        primaryLabel="Incorporar"
        primaryLoadingLabel="Incorporando..."
        primaryLoading={incorporar.isPending}
        onPrimary={() => undefined}
        schema={equipoIncorporarSchema}
        initialData={{ equipo_id: "", orden: equipos.length + 1 }}
        onSubmit={(datos) => incorporar.mutateAsync({ competenciaId, datos })}
      >
        {({ methods }) => (
          <CamposIncorporacion methods={methods} opciones={opciones} />
        )}
      </AppFormModal>

      {equipoEnEdicion ? (
        <AppFormModal<EquipoEditarForm>
          open
          onOpenChange={(abierto) => {
            if (!abierto) setEquipoEnEdicion(null);
          }}
          title={`Editar ${equipoEnEdicion.equipo_nombre}`}
          eyebrow="Cuadro"
          description="Puedes cambiar el orden o retirar la participación sin borrar su historial."
          primaryLabel="Guardar cambios"
          primaryLoadingLabel="Guardando..."
          primaryLoading={editar.isPending}
          onPrimary={() => undefined}
          schema={equipoEditarFormSchema}
          initialData={{
            orden: equipoEnEdicion.orden,
            estado: equipoEnEdicion.estado,
          }}
          onSubmit={(datos) =>
            editar.mutateAsync({
              competenciaId,
              equipoId: equipoEnEdicion.id,
              datos: {
                ...datos,
                expected_version: equipoEnEdicion.version,
              } as EquipoEditar,
            })
          }
        >
          {({ methods }) => <CamposEdicion methods={methods} />}
        </AppFormModal>
      ) : null}
    </section>
  );
}

/**
 * Los campos de la incorporación de un equipo.
 *
 * El formulario es el Modo 1 (`children`): `FormField` dibuja la etiqueta, el
 * icono y el error de cada campo. El selector es un campo CONTROLADO: su
 * valor se lee con `useController` ACOTADO a su campo, nunca con un `watch()`
 * global.
 */
function CamposIncorporacion({
  methods,
  opciones,
}: {
  methods: UseFormReturn<EquipoIncorporar>;
  opciones: readonly { value: string; label: string }[];
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: equipo } = useController({
    control: controlFormulario,
    name: "equipo_id",
  });

  return (
    <FormGrid>
      <FormField
        id="equipo-incorporar-equipo"
        label="Equipo"
        required
        icon={ListOrdered}
        span={12}
        error={errors.equipo_id?.message}
      >
        {(control) => (
          <Select
            value={equipo.value ?? ""}
            onValueChange={equipo.onChange}
            disabled={opciones.length === 0}
          >
            <SelectTrigger
              {...control}
              onBlur={equipo.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige un equipo de la competencia" />
            </SelectTrigger>
            <SelectContent>
              {opciones.map((opcion) => (
                <SelectItem key={opcion.value} value={opcion.value}>
                  {opcion.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="equipo-incorporar-orden"
        label="Orden del cuadro"
        required
        icon={Hash}
        span={12}
        helper="Es la posición manual del equipo en el cuadro."
        error={errors.orden?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("orden", { valueAsNumber: true })}
            type="number"
            min={1}
            max={999}
            step={1}
            inputMode="numeric"
          />
        )}
      </FormField>
    </FormGrid>
  );
}

/**
 * Los campos de la edición de un equipo del cuadro.
 *
 * El formulario es el Modo 1 (`children`): `FormField` dibuja la etiqueta, el
 * icono y el error de cada campo. El estado es un campo CONTROLADO: su valor
 * se lee con `useController` ACOTADO a su campo.
 */
function CamposEdicion({
  methods,
}: {
  methods: UseFormReturn<EquipoEditarForm>;
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: estado } = useController({
    control: controlFormulario,
    name: "estado",
  });

  return (
    <FormGrid>
      <FormField
        id="equipo-editar-orden"
        label="Orden del cuadro"
        required
        icon={Hash}
        span={6}
        error={errors.orden?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("orden", { valueAsNumber: true })}
            type="number"
            min={1}
            max={999}
            step={1}
            inputMode="numeric"
          />
        )}
      </FormField>

      <FormField
        id="equipo-editar-estado"
        label="Estado"
        required
        icon={ToggleRight}
        span={6}
        error={errors.estado?.message}
      >
        {(control) => (
          <Select value={estado.value ?? ""} onValueChange={estado.onChange}>
            <SelectTrigger
              {...control}
              onBlur={estado.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige el estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ACTIVO">Activo</SelectItem>
              <SelectItem value="RETIRADO">Retirado</SelectItem>
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="equipo-editar-motivo"
        label="Motivo"
        icon={NotebookPen}
        span={12}
        helper="Obligatorio al cambiar el orden o al retirar la participación."
        error={errors.motivo?.message}
      >
        {(control) => (
          <Textarea
            {...control}
            {...register("motivo")}
            rows={3}
            maxLength={500}
            placeholder="Motivo de la edición"
          />
        )}
      </FormField>
    </FormGrid>
  );
}
