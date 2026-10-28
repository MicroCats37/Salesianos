"use client";

import { Loader2, UserCheck, UserX } from "lucide-react";
import { useId, useState } from "react";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { useAsignarBeneficiarios } from "../hooks/useAsignarBeneficiarios";
import { useBeneficiariosCompra } from "../hooks/useBeneficiariosCompra";
import type {
  PaseAsignarBeneficiariosFormData,
  PaseBeneficiarioAuditado,
} from "../schemas";
import { paseAsignarBeneficiariosFormSchema } from "../schemas";
import {
  BENEFICIARIO_ACTIVA,
  paseBeneficiarioEstadoLabel,
  paseBeneficiarioTone,
  pasePersonaNombre,
  paseSlotsLibres,
  paseSlotsResumen,
} from "../utils/pase.beneficiario";
import { PaseLookupPersonaField } from "./PaseLookupPersonaField";
import { PaseQrHint } from "./PaseQrHint";
import { PaseRevocarDialog } from "./PaseRevocarDialog";

/**
 * PaseBeneficiariosPanel — the nominative rights of a paid batch.
 *
 * The panel shows the IMMUTABLE slot accounting (active, revoked, used and
 * free slots), lets the buyer assign the persons that ALREADY EXIST (resolved
 * by the exact identity lookup) and revoke a right permanently.
 *
 * The state comes from the backend: the browser never derives the accounting
 * and NEVER reuses a revoked slot.
 */

export interface PaseBeneficiariosPanelProps {
  /** The batch that owns the rights. */
  compraId: string;
}

export function PaseBeneficiariosPanel({
  compraId,
}: PaseBeneficiariosPanelProps) {
  const formId = useId();
  const [revocando, setRevocando] = useState<PaseBeneficiarioAuditado | null>(
    null,
  );

  const derechos = useBeneficiariosCompra(compraId);
  const asignar = useAsignarBeneficiarios();

  const lista = derechos.data ?? null;
  const conteos = lista
    ? {
        cantidad_pases: lista.cantidad_pases,
        activos: lista.activos,
        revocados: lista.revocados,
        slots_usados: lista.slots_usados,
        slots_disponibles: lista.slots_disponibles,
      }
    : null;

  const resumen = conteos ? paseSlotsResumen(conteos) : null;
  const libres = lista
    ? paseSlotsLibres(lista.cantidad_pases, lista.beneficiarios)
    : [];

  return (
    <section
      aria-labelledby="pase-beneficiarios-titulo"
      className="rounded-3xl border border-slate-200 bg-white p-5"
    >
      <h2
        id="pase-beneficiarios-titulo"
        className="text-lg font-black text-slate-900"
      >
        Personas que usarán los pases
      </h2>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">
        Cada pase es nominativo: se asigna a una persona que ya existe en el
        sistema. Los slots son inmutables y una revocación consume el slot para
        siempre.
      </p>

      {derechos.isPending ? (
        <output className="mt-4 block text-sm font-medium text-slate-500">
          Cargando los beneficiarios del lote...
        </output>
      ) : null}

      {derechos.error ? (
        <p
          role="alert"
          className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-800"
        >
          {derechos.error.message}
        </p>
      ) : null}

      {resumen ? (
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            {
              id: "activos",
              label: "Asignados",
              value: resumen.activos,
              clases: "border-emerald-200 bg-emerald-50 text-emerald-800",
            },
            {
              id: "revocados",
              label: "Revocados",
              value: resumen.revocados,
              clases: "border-red-200 bg-red-50 text-red-800",
            },
            {
              id: "usados",
              label: "Slots usados",
              value: resumen.usados,
              clases: "border-slate-200 bg-slate-50 text-slate-700",
            },
            {
              id: "disponibles",
              label: "Slots libres",
              value: resumen.disponibles,
              clases: "border-[#312e8e]/25 bg-[#312e8e]/[0.06] text-[#312e8e]",
            },
          ].map((contador) => (
            <div
              key={contador.id}
              className={`rounded-2xl border p-3 ${contador.clases}`}
            >
              <p className="text-[10px] font-black uppercase tracking-wider">
                {contador.label}
              </p>
              <p className="mt-1 text-xl font-black">{contador.value}</p>
            </div>
          ))}
        </div>
      ) : null}

      {resumen ? (
        <p className="mt-3 text-xs font-medium text-slate-500">
          {`Lote de ${resumen.total} pase(s). Slots libres: ${
            libres.length > 0 ? libres.join(", ") : "ninguno"
          }.`}
        </p>
      ) : null}

      <div className="mt-5">
        <GenericForm<PaseAsignarBeneficiariosFormData>
          key={`${compraId}-${resumen?.activos ?? 0}-${resumen?.revocados ?? 0}`}
          formId={formId}
          schema={paseAsignarBeneficiariosFormSchema}
          initialData={{ personas: [] }}
          isLoading={asignar.isPending}
          skipFooter
          onSubmit={async (datos) => {
            await asignar.mutateAsync({
              compraId,
              personas: datos.personas,
            });
          }}
        >
          {({ methods, isSubmitting, submissionMessage }) => {
            const personas = methods.watch("personas") ?? [];
            const excede = Boolean(
              resumen && personas.length > resumen.disponibles,
            );

            return (
              <div className="space-y-4">
                <PaseLookupPersonaField
                  limite={resumen?.disponibles ?? 0}
                  deshabilitado={isSubmitting}
                />

                {excede ? (
                  <p
                    role="alert"
                    className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800"
                  >
                    {`Solo quedan ${resumen?.disponibles} slot(s) libres: reduce la selección.`}
                  </p>
                ) : null}

                {submissionMessage?.type === "error" ? (
                  <p
                    role="alert"
                    className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-800"
                  >
                    {submissionMessage.message}
                  </p>
                ) : null}

                <Button
                  type="submit"
                  form={formId}
                  disabled={
                    isSubmitting ||
                    excede ||
                    resumen?.disponibles === 0 ||
                    personas.length === 0
                  }
                  className="btn-brand-gradient w-full rounded-full font-black text-white"
                >
                  {isSubmitting ? (
                    <Loader2
                      className="mr-2 size-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : null}
                  Asignar a las personas seleccionadas
                </Button>
              </div>
            );
          }}
        </GenericForm>
      </div>

      {lista && lista.beneficiarios.length > 0 ? (
        <div className="mt-6">
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">
            Pases asignados
          </h3>
          <ul className="mt-2 space-y-2">
            {lista.beneficiarios.map((beneficiario) => {
              const tono = paseBeneficiarioTone(beneficiario.estado);

              return (
                <li
                  key={beneficiario.persona_id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 p-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    {tono === "activa" ? (
                      <UserCheck
                        className="size-5 shrink-0 text-emerald-600"
                        aria-hidden="true"
                      />
                    ) : (
                      <UserX
                        className="size-5 shrink-0 text-red-600"
                        aria-hidden="true"
                      />
                    )}
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-slate-900">
                        {`Slot ${beneficiario.slot} · ${pasePersonaNombre(beneficiario)}`}
                      </p>
                      <p className="text-xs font-medium text-slate-500">
                        {`${beneficiario.tipo_documento} ${beneficiario.numero_documento}`}
                      </p>
                      {beneficiario.motivo_revocacion ? (
                        <p className="mt-1 text-xs font-medium text-red-700">
                          {`Motivo de la revocación: ${beneficiario.motivo_revocacion}`}
                        </p>
                      ) : null}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-wider ${
                        tono === "activa"
                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                          : "border-red-200 bg-red-50 text-red-700"
                      }`}
                    >
                      {paseBeneficiarioEstadoLabel(beneficiario.estado)}
                    </span>

                    {beneficiario.estado === BENEFICIARIO_ACTIVA ? (
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => setRevocando(beneficiario)}
                        className="font-black"
                      >
                        Revocar
                      </Button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <div className="mt-5">
        <PaseQrHint />
      </div>

      <PaseRevocarDialog
        open={revocando !== null}
        onOpenChange={(abierto) => {
          if (!abierto) setRevocando(null);
        }}
        compraId={compraId}
        beneficiario={revocando}
      />
    </section>
  );
}
