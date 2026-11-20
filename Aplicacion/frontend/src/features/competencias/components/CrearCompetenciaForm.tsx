"use client";

import { CalendarDays, Plus, Trophy, Users } from "lucide-react";
import { useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
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
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useCrearCompetencia } from "../hooks/useCompetencias";
import {
  type CompetenciaCrear,
  competenciaCrearSchema,
} from "../schemas/competencia.schema";

interface OpcionCatalogo {
  id: string;
  nombre: string;
}

const valoresIniciales: CompetenciaCrear = {
  nombre: "",
  fecha: "",
  disciplina_id: "",
  categoria_id: "",
};

export function CrearCompetenciaForm({
  disciplinas,
  categorias,
}: {
  disciplinas: readonly OpcionCatalogo[];
  categorias: readonly OpcionCatalogo[];
}) {
  const [open, setOpen] = useState(false);
  const crear = useCrearCompetencia();

  return (
    <>
      <Button
        type="button"
        onClick={() => setOpen(true)}
        disabled={!disciplinas.length || !categorias.length}
      >
        <Plus className="size-4" aria-hidden="true" />
        Nueva competencia
      </Button>
      <AppFormModal<CompetenciaCrear>
        open={open}
        onOpenChange={setOpen}
        title="Nueva competencia"
        eyebrow="Competencias"
        description="La competencia se crea en la edición vigente. El servidor valida disciplina, categoría y fecha."
        primaryLabel="Crear competencia"
        primaryLoadingLabel="Creando..."
        primaryLoading={crear.isPending}
        primaryDisabled={!disciplinas.length || !categorias.length}
        onPrimary={() => undefined}
        schema={competenciaCrearSchema}
        initialData={valoresIniciales}
        onSubmit={(data) => crear.mutateAsync(data)}
      >
        {({ methods }) => (
          <CamposCompetencia
            methods={methods}
            disciplinas={disciplinas}
            categorias={categorias}
          />
        )}
      </AppFormModal>
    </>
  );
}

/**
 * Los campos de la competencia.
 *
 * El formulario es el Modo 1 (`children`): `FormField` dibuja la etiqueta, el
 * icono y el error de cada campo. Los dos selectores son campos CONTROLADOS:
 * su valor se lee con `useController` ACOTADO a su campo, nunca con un
 * `watch()` global.
 */
function CamposCompetencia({
  methods,
  disciplinas,
  categorias,
}: {
  methods: UseFormReturn<CompetenciaCrear>;
  disciplinas: readonly OpcionCatalogo[];
  categorias: readonly OpcionCatalogo[];
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: disciplina } = useController({
    control: controlFormulario,
    name: "disciplina_id",
  });
  const { field: categoria } = useController({
    control: controlFormulario,
    name: "categoria_id",
  });

  return (
    <FormGrid>
      <FormField
        id="competencia-nombre"
        label="Nombre"
        required
        icon={Trophy}
        span={12}
        error={errors.nombre?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("nombre")}
            placeholder="Ej. Copa Promoción 2016"
            maxLength={200}
          />
        )}
      </FormField>

      <FormField
        id="competencia-disciplina"
        label="Disciplina"
        required
        icon={Trophy}
        span={6}
        error={errors.disciplina_id?.message}
      >
        {(control) => (
          <Select
            value={disciplina.value ?? ""}
            onValueChange={disciplina.onChange}
            disabled={disciplinas.length === 0}
          >
            <SelectTrigger
              {...control}
              onBlur={disciplina.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige la disciplina" />
            </SelectTrigger>
            <SelectContent>
              {disciplinas.map((opcion) => (
                <SelectItem key={opcion.id} value={opcion.id}>
                  {opcion.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="competencia-categoria"
        label="Categoría"
        required
        icon={Users}
        span={6}
        error={errors.categoria_id?.message}
      >
        {(control) => (
          <Select
            value={categoria.value ?? ""}
            onValueChange={categoria.onChange}
            disabled={categorias.length === 0}
          >
            <SelectTrigger
              {...control}
              onBlur={categoria.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige la categoría" />
            </SelectTrigger>
            <SelectContent>
              {categorias.map((opcion) => (
                <SelectItem key={opcion.id} value={opcion.id}>
                  {opcion.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="competencia-fecha"
        label="Fecha"
        required
        icon={CalendarDays}
        span={12}
        error={errors.fecha?.message}
      >
        {(control) => <Input {...control} {...register("fecha")} type="date" />}
      </FormField>
    </FormGrid>
  );
}
