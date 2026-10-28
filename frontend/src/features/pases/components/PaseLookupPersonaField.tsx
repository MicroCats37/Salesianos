"use client";

import { Loader2, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { useController } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useResolverPersona } from "../hooks/useResolverPersona";
import type { PersonaResuelta } from "../schemas";
import { pasePersonaYaSeleccionada } from "../utils/pase.beneficiario";

/**
 * PaseLookupPersonaField — the EXACT lookup of the persons that receive the
 * passes.
 *
 * It is a SMART FIELD: the selection lives in the context of `GenericForm`
 * (through `useController`) and the component NEVER owns a value and NEVER
 * validates by itself (`contract/smart.md` §2).
 *
 * The lookup resolves a person that ALREADY EXISTS through the exact
 * identity endpoint: the component NEVER creates a person, NEVER accepts
 * free text as a person and NEVER queries the external document registry.
 */

/** The document types the application recognizes — backend `TipoDocumentoChoices`. */
const TIPOS_DOCUMENTO = [
  { valor: "DNI", etiqueta: "DNI" },
  { valor: "CE", etiqueta: "Carnet de extranjería" },
  { valor: "PAS", etiqueta: "Pasaporte" },
] as const;

export interface PaseLookupPersonaFieldProps {
  /** How many persons can still be added (the free slots). */
  limite: number;
  /** Whether the lookup is blocked (a mutation is in flight). */
  deshabilitado?: boolean;
}

export function PaseLookupPersonaField({
  limite,
  deshabilitado = false,
}: PaseLookupPersonaFieldProps) {
  const [tipoDocumento, setTipoDocumento] = useState<string>("DNI");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const resolver = useResolverPersona();
  const { field } = useController<{ personas: PersonaResuelta[] }>({
    name: "personas",
  });

  const personas = Array.isArray(field.value) ? field.value : [];
  const sinSlots = limite <= 0;
  const noEncontrada = resolver.error?.status === 404;

  async function handleBuscar() {
    const numero = numeroDocumento.trim();
    if (!numero || sinSlots || deshabilitado) return;

    try {
      const persona = await resolver.mutateAsync({
        tipoDocumento,
        numeroDocumento: numero,
      });

      if (pasePersonaYaSeleccionada(personas, persona.persona_id)) return;

      field.onChange([...personas, persona]);
      setNumeroDocumento("");
    } catch {
      // The failure is already reported by the hook (toast) and the 404
      // renders the "not found" state: the component never handles raw errors.
    }
  }

  function quitar(personaId: string) {
    field.onChange(
      personas.filter((persona) => persona.persona_id !== personaId),
    );
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="pase-persona-tipo" className="text-sm font-bold">
          Tipo de documento
        </Label>
        <select
          id="pase-persona-tipo"
          value={tipoDocumento}
          disabled={deshabilitado}
          onChange={(evento) => setTipoDocumento(evento.target.value)}
          className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm font-bold text-slate-900 focus:border-[#312e8e] focus:outline-none focus:ring-2 focus:ring-[#312e8e]/30"
        >
          {TIPOS_DOCUMENTO.map((tipo) => (
            <option key={tipo.valor} value={tipo.valor}>
              {tipo.etiqueta}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <Label htmlFor="pase-persona-documento" className="text-sm font-bold">
          Número de documento
        </Label>
        <p
          id="pase-persona-documento-ayuda"
          className="text-xs font-medium text-slate-500"
        >
          La búsqueda es EXACTA: sólo encuentra personas ya registradas en el
          sistema. Nunca crea personas ni consulta el registro externo.
        </p>
        <div className="mt-2 flex items-stretch gap-2">
          <div className="flex-1">
            <Input
              id="pase-persona-documento"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              value={numeroDocumento}
              disabled={deshabilitado || sinSlots}
              placeholder="12345678"
              aria-describedby="pase-persona-documento-ayuda"
              onChange={(evento) => setNumeroDocumento(evento.target.value)}
              onKeyDown={(evento) => {
                if (evento.key === "Enter") {
                  evento.preventDefault();
                  void handleBuscar();
                }
              }}
            />
          </div>
          <Button
            type="button"
            onClick={() => {
              void handleBuscar();
            }}
            disabled={
              deshabilitado ||
              sinSlots ||
              numeroDocumento.trim().length === 0 ||
              resolver.isPending
            }
            aria-label="Buscar la persona por documento"
            className="shrink-0"
          >
            {resolver.isPending ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Search className="size-4" aria-hidden="true" />
            )}
          </Button>
        </div>
      </div>

      {sinSlots ? (
        <p className="text-sm font-medium text-slate-600">
          No quedan slots libres en este lote: no se pueden añadir más personas.
        </p>
      ) : null}

      {noEncontrada ? (
        <output className="block rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
          No hay ninguna persona registrada con ese documento.
        </output>
      ) : null}

      {personas.length > 0 ? (
        <ul className="space-y-2" aria-label="Personas seleccionadas">
          {personas.map((persona) => (
            <li
              key={persona.persona_id}
              className="flex items-center justify-between gap-3 rounded-2xl border border-[#312e8e]/30 bg-[#312e8e]/[0.05] p-3"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-bold text-slate-900">
                  {persona.nombre_completo}
                </p>
                <p className="text-xs font-medium text-slate-500">
                  {`${persona.tipo_documento} ${persona.numero_documento}`}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Quitar a ${persona.nombre_completo} de la selección`}
                disabled={deshabilitado}
                onClick={() => quitar(persona.persona_id)}
              >
                <Trash2 className="size-4" aria-hidden="true" />
              </Button>
            </li>
          ))}
        </ul>
      ) : null}

      <p className="text-xs font-medium text-slate-500">
        {`Personas seleccionadas: ${personas.length} de ${limite} slot(s) libres.`}
      </p>
    </div>
  );
}
