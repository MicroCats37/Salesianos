"use client";

import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { CodigoErrorMedio, Patrocinador } from "../types/patrocinador.types";

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
  /** The sponsor being edited. `undefined` means a new sponsor. */
  patrocinador?: Patrocinador;
  /** The media error the server declared, if it declared one. */
  errorMedio?: CodigoErrorMedio;
  /** The save. It is OPTIONAL: without it the form says why. */
  onGuardar?: (datos: DatosPatrocinador) => void;
  /** Whether the save is in flight. */
  ocupado?: boolean;
}

/** What the form collects. The FILES travel as they are: no `FormData`. */
export interface DatosPatrocinador {
  nombre: string;
  slug: string;
  descripcion: string;
  sitio_web: string;
  visible: boolean;
  logo: File | null;
  imagenes: File[];
}

/**
 * FormularioPatrocinador - the record of a sponsor.
 *
 * The form collects the DATA and hands the FILES over as they are. It never
 * builds a `FormData` and never speaks to the network: the multipart
 * protocol is the one of the backend (`FREEZE-MD-1.0.0`) and the transport
 * belongs to `salesianos-api-data`, which is a forbidden root of this packet.
 *
 * The gallery is ORDERED: the order in which the operator chooses the files
 * is the order in which they travel, and it is the order the backend makes
 * canonical (`FR-06` §2.4).
 */
export function FormularioPatrocinador({
  patrocinador,
  errorMedio,
  onGuardar,
  ocupado = false,
}: FormularioPatrocinadorProps) {
  const [nombre, setNombre] = useState(patrocinador?.nombre ?? "");
  const [slug, setSlug] = useState(patrocinador?.slug ?? "");
  const [descripcion, setDescripcion] = useState(patrocinador?.descripcion ?? "");
  const [sitioWeb, setSitioWeb] = useState(patrocinador?.sitio_web ?? "");
  const [visible, setVisible] = useState(patrocinador?.visible ?? true);
  const [logo, setLogo] = useState<File | null>(null);
  const [imagenes, setImagenes] = useState<File[]>([]);

  const idLogo = "patrocinador-logo";
  const idImagenes = "patrocinador-imagenes";
  const idAyudaLogo = "patrocinador-logo-ayuda";
  const idAyudaImagenes = "patrocinador-imagenes-ayuda";

  return (
    <form
      className="flex flex-col gap-5"
      onSubmit={(evento) => {
        evento.preventDefault();
        if (!onGuardar || ocupado) return;
        onGuardar({
          nombre: nombre.trim(),
          slug: slug.trim(),
          descripcion,
          sitio_web: sitioWeb.trim(),
          visible,
          logo,
          imagenes,
        });
      }}
    >
      {errorMedio ? (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 p-3"
        >
          <AlertCircle
            className="mt-0.5 size-4 shrink-0 text-destructive"
            aria-hidden="true"
          />
          <p className="text-sm text-foreground">{ERRORES_MEDIO[errorMedio]}</p>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="patrocinador-nombre">Nombre</Label>
          <Input
            id="patrocinador-nombre"
            value={nombre}
            onChange={(evento) => setNombre(evento.target.value)}
            maxLength={200}
            required
            disabled={ocupado}
            className="min-h-11"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="patrocinador-slug">Identificador en la edición</Label>
          <Input
            id="patrocinador-slug"
            value={slug}
            onChange={(evento) => setSlug(evento.target.value)}
            maxLength={200}
            required
            disabled={ocupado}
            aria-describedby="patrocinador-slug-ayuda"
            className="min-h-11"
          />
          <p
            id="patrocinador-slug-ayuda"
            className="text-caption text-muted-foreground"
          >
            En minúsculas y con guiones, por ejemplo
            <code className="font-mono">colegio-norte</code>. El protocolo de
            carga busca fichas con guion bajo y este identificador no puede
            colisionar con ellas.
          </p>
        </div>

        <div className="flex flex-col gap-1.5 md:col-span-2">
          <Label htmlFor="patrocinador-descripcion">Descripción</Label>
          <Textarea
            id="patrocinador-descripcion"
            value={descripcion}
            onChange={(evento) => setDescripcion(evento.target.value)}
            maxLength={5000}
            disabled={ocupado}
            rows={4}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="patrocinador-sitio-web">Sitio web</Label>
          <Input
            id="patrocinador-sitio-web"
            type="url"
            value={sitioWeb}
            onChange={(evento) => setSitioWeb(evento.target.value)}
            maxLength={300}
            disabled={ocupado}
            aria-describedby="patrocinador-sitio-web-ayuda"
            className="min-h-11"
          />
          <p
            id="patrocinador-sitio-web-ayuda"
            className="text-caption text-muted-foreground"
          >
            Opcional. La dirección completa, con el protocolo.
          </p>
        </div>

        <div className="flex items-end">
          <div className="flex items-center gap-2">
            <Checkbox
              id="patrocinador-visible"
              checked={visible}
              onCheckedChange={(valor) => setVisible(valor === true)}
              disabled={ocupado}
            />
            <Label htmlFor="patrocinador-visible" className="text-sm">
              Visible en la página pública
            </Label>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={idLogo}>Logo de identidad</Label>
          <Input
            id={idLogo}
            type="file"
            accept={TIPOS_ACEPTADOS}
            disabled={ocupado}
            aria-describedby={idAyudaLogo}
            className="min-h-11"
            onChange={(evento) => setLogo(evento.target.files?.[0] ?? null)}
          />
          <p id={idAyudaLogo} className="text-caption text-muted-foreground">
            Opcional. Formatos {TIPOS_ACEPTADOS}, hasta {TAMANO_MAXIMO}. El
            servidor comprueba el contenido real del archivo, no el tipo que
            declara el navegador.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={idImagenes}>Galería de piezas</Label>
          <Input
            id={idImagenes}
            type="file"
            accept={TIPOS_ACEPTADOS}
            multiple
            disabled={ocupado}
            aria-describedby={idAyudaImagenes}
            className="min-h-11"
            onChange={(evento) =>
              setImagenes(Array.from(evento.target.files ?? []))
            }
          />
          <p id={idAyudaImagenes} className="text-caption text-muted-foreground">
            El orden en el que elijas los archivos es el orden en el que se
            publican. Formatos {TIPOS_ACEPTADOS}, hasta {TAMANO_MAXIMO} cada
            uno.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Button
          type="submit"
          disabled={!onGuardar || ocupado}
          className="min-h-11 sm:w-fit"
        >
          {ocupado ? "Guardando…" : "Guardar el patrocinador"}
        </Button>
        {!onGuardar ? (
          <p className="text-caption text-muted-foreground">
            El servicio de patrocinadores todavía no está conectado en el
            backend: el formulario se puede completar, pero el guardado no
            sale de este dispositivo.
          </p>
        ) : null}
      </div>
    </form>
  );
}
