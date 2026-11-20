"use client";

import {
  AlignLeft,
  Eye,
  Globe,
  Hash,
  Image as ImageIcon,
  Images,
  TriangleAlert,
  Type,
} from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { FormularioPatrocinadorDatos } from "../schemas/patrocinador.schema";
import type { CodigoErrorMedio } from "../types/patrocinador.types";

/**
 * The media contract of the edition (`FREEZE-MD-1.0.0`,
 * `Aplicacion/backend/core/media.py`).
 *
 * The allowlist and the cap are the ones the server publishes: the file
 * input announces them so the operator knows what is accepted BEFORE
 * choosing a file. The server checks the SIGNATURE of the file, never the
 * declared type, and it is the server that refuses.
 */
const TIPOS_ACEPTADOS = "image/jpeg, image/png, image/webp";
const TAMANO_MAXIMO = "5 MiB";

/**
 * The wording of the media errors of `RT-MD-02`.
 *
 * The codes come from the ledger
 * (`evidence/contracts/route-to-wrapper-ledger.csv`); the wording says what
 * happened and what to do, and it never contradicts the rule of the server.
 */
const ERRORES_MEDIO: Record<CodigoErrorMedio, string> = {
  MEDIA_TIPO_NO_PERMITIDO: `El tipo del archivo no está permitido. Solo se aceptan ${TIPOS_ACEPTADOS}.`,
  MEDIA_ARCHIVO_HUERFANO:
    "Se envió un archivo que no estaba declarado en la ficha. Vuelve a elegir las piezas y guarda de nuevo.",
  MEDIA_TOKEN_NO_RESOLTO:
    "No se pudo asociar un archivo con su lugar en la ficha. Vuelve a elegir las piezas.",
  MEDIA_TOKEN_DUPLICADO:
    "La misma imagen aparece dos veces en la ficha. Vuelve a elegir las piezas.",
  MEDIA_TAMANO_EXCEDIDO: `La imagen supera el tamaño máximo de ${TAMANO_MAXIMO}.`,
  MEDIA_NO_PERMITIDO: "El servidor no permitió esta operación de media.",
};

export interface FormularioPatrocinadorProps {
  /** The methods of the form that owns the record. */
  methods: UseFormReturn<FormularioPatrocinadorDatos>;
  /** The media error the server declared, if it declared one. */
  errorMedio?: CodigoErrorMedio;
  /** Whether the save is in flight. */
  ocupado?: boolean;
}

/**
 * FormularioPatrocinador - the fields of the record of a sponsor.
 *
 * The form collects the DATA and hands the FILES over as they are. It never
 * builds a `FormData` and never speaks to the network: the multipart
 * protocol is the one of the backend (`FREEZE-MD-1.0.0`) and the transport
 * belongs to the generic hooks.
 *
 * The gallery is ORDERED: the order in which the operator chooses the files
 * is the order in which they travel, and it is the order the backend makes
 * canonical (`FR-06` §2.4).
 *
 * Every field is drawn by `FormField`: the label, the icon and the error
 * live there, and the help of each field is its `helper`.
 */
export function FormularioPatrocinador({
  methods,
  errorMedio,
  ocupado = false,
}: FormularioPatrocinadorProps) {
  const {
    register,
    setValue,
    watch,
    formState: { errors },
  } = methods;

  const visible = watch("visible");

  return (
    <div className="flex flex-col gap-5">
      {errorMedio ? (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 p-3"
        >
          <TriangleAlert
            className="mt-0.5 size-4 shrink-0 text-destructive"
            aria-hidden="true"
          />
          <p className="text-sm text-foreground">{ERRORES_MEDIO[errorMedio]}</p>
        </div>
      ) : null}

      <FormGrid>
        <FormField
          id="patrocinador-nombre"
          label="Nombre"
          required
          icon={Type}
          span={6}
          error={errors.nombre?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("nombre")}
              maxLength={200}
              required
              disabled={ocupado}
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-slug"
          label="Identificador en la edición"
          required
          icon={Hash}
          span={6}
          helper="En minúsculas y con guiones, por ejemplo colegio-norte. El protocolo de carga busca fichas con guion bajo y este identificador no puede colisionar con ellas."
          error={errors.slug?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("slug")}
              maxLength={200}
              required
              disabled={ocupado}
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-descripcion"
          label="Descripción"
          icon={AlignLeft}
          span={12}
          error={errors.descripcion?.message}
        >
          {(control) => (
            <Textarea
              {...control}
              {...register("descripcion")}
              maxLength={5000}
              disabled={ocupado}
              rows={4}
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-sitio-web"
          label="Sitio web"
          icon={Globe}
          span={6}
          helper="Opcional. La dirección completa, con el protocolo."
          error={errors.sitio_web?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("sitio_web")}
              type="url"
              maxLength={300}
              disabled={ocupado}
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-visible"
          label="Visible en la página pública"
          icon={Eye}
          span={6}
          helper="Un patrocinador oculto no aparece en la web, pero su ficha se conserva."
          error={errors.visible?.message}
        >
          {(control) => (
            <Checkbox
              {...control}
              checked={visible}
              onCheckedChange={(valor) =>
                setValue("visible", valor === true, { shouldValidate: true })
              }
              disabled={ocupado}
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-logo"
          label="Logo de identidad"
          icon={ImageIcon}
          span={6}
          helper={`Opcional. Formatos ${TIPOS_ACEPTADOS}, hasta ${TAMANO_MAXIMO}. El servidor comprueba el contenido real del archivo, no el tipo que declara el navegador.`}
          error={errors.logo?.message}
        >
          {(control) => (
            <Input
              {...control}
              id="patrocinador-logo"
              type="file"
              accept={TIPOS_ACEPTADOS}
              disabled={ocupado}
              onChange={(evento) =>
                setValue("logo", evento.target.files?.[0] ?? null, {
                  shouldValidate: true,
                })
              }
            />
          )}
        </FormField>

        <FormField
          id="patrocinador-imagenes"
          label="Galería de piezas"
          icon={Images}
          span={6}
          helper={`El orden en el que elijas los archivos es el orden en el que se publican. Formatos ${TIPOS_ACEPTADOS}, hasta ${TAMANO_MAXIMO} cada uno.`}
          error={errors.imagenes?.message}
        >
          {(control) => (
            <Input
              {...control}
              id="patrocinador-imagenes"
              type="file"
              accept={TIPOS_ACEPTADOS}
              multiple
              disabled={ocupado}
              onChange={(evento) =>
                setValue("imagenes", Array.from(evento.target.files ?? []), {
                  shouldValidate: true,
                })
              }
            />
          )}
        </FormField>
      </FormGrid>
    </div>
  );
}
