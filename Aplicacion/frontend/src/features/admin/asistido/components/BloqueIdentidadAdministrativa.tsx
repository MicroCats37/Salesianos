"use client";

import { Fingerprint, Hash, Loader2, Search, User, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useController, useFormContext, useWatch } from "react-hook-form";
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
import { getErrorMessage } from "@/errors";
import { useResolverPersona } from "@/features/auth/hooks";
import type { IdentidadAdministrativaCampos } from "../schemas/asistido.schema";

/**
 * The ADMINISTRATIVE identity block: ONE Smart Field for the three forms
 * that ask for a civil document.
 *
 * ## What it owns
 *
 * The UX of resolving an EXACT document: the administrator searches, and the
 * block answers with ONE of three states:
 *
 * | State | What it means | What it does with the names |
 * |---|---|---|
 * | `SIN_CONSULTAR` | nobody searched yet | the name fields are NOT shown |
 * | `ENCONTRADA` | the padrón already has that person | the canonical names are SHOWN and the identity is REUSED |
 * | `NO_ENCONTRADA` | the padrón does not have that person | the name, the surname and the gender fields are REVEALED and required |
 *
 * ## What it does NOT do
 *
 * - It NEVER creates an identity: it only READS the padrón. The command
 *   decides whether the person has to be registered.
 * - It NEVER asks for the names of a person that already exists: the padrón
 *   is the authority and its names are not editable from here.
 * - It NEVER shows a LABEL twice and it never registers a field twice: every
 *   control of this block is bound ONCE, with `useController`.
 */

export interface BloqueIdentidadAdministrativaProps {
  /**
   * The prefix of the ids of the block.
   *
   * The three forms of the area live in the same page: the prefix keeps the
   * ids unique and the labels associated with their own control.
   */
  idPrefijo: string;
  /** Whether the block is locked (a command in flight). */
  bloqueado?: boolean;
}

/** The vocabulary of the type of document. */
const TIPOS_DOCUMENTO = [
  { etiqueta: "DNI", valor: "DNI" },
  { etiqueta: "Carné de extranjería", valor: "CE" },
  { etiqueta: "Pasaporte", valor: "PAS" },
];

/** The vocabulary of the gender: the owner is the DOMAIN. */
const GENEROS = [
  { etiqueta: "Masculino", valor: "M" },
  { etiqueta: "Femenino", valor: "F" },
];

export function BloqueIdentidadAdministrativa({
  idPrefijo,
  bloqueado = false,
}: BloqueIdentidadAdministrativaProps) {
  const {
    control,
    setValue,
    formState: { errors },
  } = useFormContext<IdentidadAdministrativaCampos>();

  const resolver = useResolverPersona();

  // Every control of the block is bound ONCE. The hooks are NOT conditional:
  // the name fields are only RENDERED when the identity has to be registered.
  const { field: tipoDocumento } = useController({
    control,
    name: "tipo_documento",
  });
  const { field: numeroDocumento } = useController({
    control,
    name: "numero_documento",
  });
  const { field: nombres } = useController({ control, name: "nombres" });
  const { field: apellidos } = useController({ control, name: "apellidos" });
  const { field: genero } = useController({ control, name: "genero" });

  const estado =
    useWatch({ control, name: "estado_identidad" }) ?? "SIN_CONSULTAR";
  const nombresResueltos = useWatch({ control, name: "nombres" }) ?? "";
  const apellidosResueltos = useWatch({ control, name: "apellidos" }) ?? "";

  const [mensaje, setMensaje] = useState<string | null>(null);
  const [fallo, setFallo] = useState<string | null>(null);

  const esDni = tipoDocumento.value === "DNI";
  const maximoDocumento = esDni
    ? 8
    : tipoDocumento.value === "CE"
      ? 9
      : 20;
  const placeholderDocumento = esDni
    ? "12345678"
    : tipoDocumento.value === "CE"
      ? "123456789"
      : "ABC123456";
  const modoEntradaDocumento =
    tipoDocumento.value === "PAS" ? "text" : "numeric";

  /**
   * The document the CURRENT resolution belongs to.
   *
   * When the administrator edits the document, the resolution of the
   * previous one stops being valid: the names that were hydrated belong to
   * another person and the gender that was declared may be wrong.
   */
  const documentoVisto = useRef<string | null>(null);

  const clave = `${tipoDocumento.value}|${numeroDocumento.value.trim()}`;

  useEffect(() => {
    const anterior = documentoVisto.current;
    documentoVisto.current = clave;

    // CE and passport are entered manually, just like registration. They do
    // not depend on the DNI lookup service to reveal the civil fields.
    if (anterior === null) {
      if (!esDni) {
        setValue("estado_identidad", "NO_ENCONTRADA", {
          shouldValidate: true,
        });
        setMensaje(
          "Ingresa los nombres, apellidos y género tal como aparecen en el documento.",
        );
      }
      return;
    }
    // The document did not change: the resolution is still valid.
    if (anterior === clave) return;

    setValue("nombres", "", { shouldValidate: false });
    setValue("apellidos", "", { shouldValidate: false });
    setValue("genero", "", { shouldValidate: false });
    setValue("estado_identidad", esDni ? "SIN_CONSULTAR" : "NO_ENCONTRADA", {
      shouldValidate: true,
    });
    setMensaje(
      esDni
        ? null
        : "Ingresa los nombres, apellidos y género tal como aparecen en el documento.",
    );
    setFallo(null);
  }, [clave, esDni, setValue]);

  async function buscar() {
    const numero = numeroDocumento.value.trim();

    if (!numero) {
      setFallo("Escribe el número de documento antes de buscar la identidad.");
      setMensaje(null);
      return;
    }

    setFallo(null);
    setMensaje("Buscando la identidad en el padrón…");

    try {
      const resultado = await resolver.mutateAsync({
        tipo_documento: tipoDocumento.value,
        numero_documento: numero,
      });

      setValue("nombres", resultado.nombres ?? "", {
        shouldDirty: true,
        shouldValidate: true,
      });
      setValue("apellidos", resultado.apellidos ?? "", {
        shouldDirty: true,
        shouldValidate: true,
      });

      if (resultado.persistida) {
        setValue("estado_identidad", "ENCONTRADA", {
          shouldDirty: true,
          shouldValidate: true,
        });
        setMensaje(
          "El padrón ya tiene a esta persona: se reutiliza su identidad y sus datos no se modifican.",
        );
        return;
      }

      setValue("estado_identidad", "NO_ENCONTRADA", {
        shouldDirty: true,
        shouldValidate: true,
      });
      setMensaje(
        resultado.nombres
          ? "No está en el padrón, pero la fuente externa conoce sus nombres: revísalos y declara el género para registrarla."
          : "No hay ninguna persona con ese documento: declara sus nombres, apellidos y género para registrarla.",
      );
    } catch (error) {
      setValue("estado_identidad", "SIN_CONSULTAR", {
        shouldDirty: true,
        shouldValidate: true,
      });
      setMensaje(null);
      setFallo(
        getErrorMessage(error) ??
          "No se pudo consultar la identidad del documento.",
      );
    }
  }

  const encontrada = estado === "ENCONTRADA";
  const registrar = estado === "NO_ENCONTRADA";
  const nombreRegistrado = `${nombresResueltos} ${apellidosResueltos}`.trim();

  return (
    <div className="col-span-12 flex flex-col gap-3">
      <FormGrid>
        <FormField
          id={`${idPrefijo}-tipo-documento`}
          label="Tipo de documento"
          required
          icon={Fingerprint}
          span={4}
          error={errors.tipo_documento?.message}
        >
          {(control) => (
            <Select
              value={tipoDocumento.value}
              onValueChange={tipoDocumento.onChange}
              disabled={bloqueado}
            >
              <SelectTrigger
                id={control.id}
                aria-invalid={control["aria-invalid"]}
                aria-describedby={control["aria-describedby"]}
                onBlur={tipoDocumento.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige el tipo" />
              </SelectTrigger>
              <SelectContent>
                {TIPOS_DOCUMENTO.map((opcion) => (
                  <SelectItem key={opcion.valor} value={opcion.valor}>
                    {opcion.etiqueta}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id={`${idPrefijo}-numero-documento`}
          label="Número de documento"
          required
          icon={Hash}
          span={8}
          helper="Busca la identidad: el padrón decide si se reutiliza o se registra."
          error={errors.numero_documento?.message}
        >
          {(control) => (
            <div className="flex items-stretch gap-2">
              <Input
                {...numeroDocumento}
                id={control.id}
                aria-invalid={control["aria-invalid"]}
                aria-describedby={control["aria-describedby"]}
                disabled={bloqueado}
                inputMode={modoEntradaDocumento}
                autoComplete="off"
                placeholder={placeholderDocumento}
                maxLength={maximoDocumento}
                onChange={(evento) => {
                  const valor = esDni || tipoDocumento.value === "CE"
                    ? evento.target.value.replace(/\D/g, "")
                    : evento.target.value
                        .replace(/[^a-zA-Z0-9]/g, "")
                        .toUpperCase();
                  numeroDocumento.onChange(valor.slice(0, maximoDocumento));
                }}
              />
              {esDni ? (
                <Button
                  type="button"
                  variant="default"
                  disabled={
                    bloqueado ||
                    resolver.isPending ||
                    numeroDocumento.value.length !== 8
                  }
                  onClick={buscar}
                  aria-label="Buscar la identidad del documento"
                  className="min-h-11 shrink-0 gap-2 rounded-xl px-4"
                >
                  {resolver.isPending ? (
                    <Loader2
                      className="size-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <Search className="size-4" aria-hidden="true" />
                  )}
                  {resolver.isPending ? "Buscando..." : "Buscar persona"}
                </Button>
              ) : null}
            </div>
          )}
        </FormField>

        <div
          aria-live="polite"
          aria-atomic="true"
          aria-busy={resolver.isPending}
          className="col-span-12"
        >
          {fallo ? (
            <p role="alert" className="text-caption text-destructive">
              {fallo}
            </p>
          ) : mensaje ? (
            <p className="text-caption text-muted-foreground">{mensaje}</p>
          ) : null}
        </div>

        {encontrada ? (
          <div className="col-span-12 rounded-xl border border-primary/30 bg-primary/5 p-3">
            <p className="text-sm font-semibold text-foreground">
              {nombreRegistrado || "Persona registrada"}
            </p>
            <p className="text-caption text-muted-foreground">
              Ya está en el padrón: se reutiliza su identidad y sus datos no se
              modifican.
            </p>
          </div>
        ) : null}

        {registrar ? (
          <>
            <FormField
              id={`${idPrefijo}-nombres`}
              label="Nombres"
              required
              icon={User}
              span={6}
              helper="La persona se registrará en el padrón con estos datos."
              error={errors.nombres?.message}
            >
              {(control) => (
                <Input
                  {...nombres}
                  id={control.id}
                  aria-invalid={control["aria-invalid"]}
                  aria-describedby={control["aria-describedby"]}
                  disabled={bloqueado}
                />
              )}
            </FormField>

            <FormField
              id={`${idPrefijo}-apellidos`}
              label="Apellidos"
              required
              icon={Users}
              span={6}
              error={errors.apellidos?.message}
            >
              {(control) => (
                <Input
                  {...apellidos}
                  id={control.id}
                  aria-invalid={control["aria-invalid"]}
                  aria-describedby={control["aria-describedby"]}
                  disabled={bloqueado}
                />
              )}
            </FormField>

            <FormField
              id={`${idPrefijo}-genero`}
              label="Género"
              required
              icon={User}
              span={12}
              helper="La disciplina lo exige para admitir a la persona."
              error={errors.genero?.message}
            >
              {(control) => (
                <Select
                  value={genero.value}
                  onValueChange={genero.onChange}
                  disabled={bloqueado}
                >
                  <SelectTrigger
                    id={control.id}
                    aria-invalid={control["aria-invalid"]}
                    aria-describedby={control["aria-describedby"]}
                    onBlur={genero.onBlur}
                    className="w-full"
                  >
                    <SelectValue placeholder="Elige el género" />
                  </SelectTrigger>
                  <SelectContent>
                    {GENEROS.map((opcion) => (
                      <SelectItem key={opcion.valor} value={opcion.valor}>
                        {opcion.etiqueta}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </FormField>
          </>
        ) : null}
      </FormGrid>
    </div>
  );
}
