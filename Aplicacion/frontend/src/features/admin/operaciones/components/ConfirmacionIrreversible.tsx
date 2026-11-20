"use client";

import { type ReactNode, useId, useState } from "react";
import { FormField } from "@/components/forms/FormField";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";

export interface ConfirmacionIrreversibleProps {
  /** Whether the confirmation is open. */
  abierto: boolean;
  /** Called when the confirmation opens or closes. */
  onAbiertoChange: (abierto: boolean) => void;
  /** The name of the action. */
  titulo: string;
  /**
   * The CONCRETE effect of the action.
   *
   * `SH-03` S-10: the confirmation names the effect. "¿Está seguro?" without
   * naming what happens is forbidden.
   */
  efecto: string;
  /** The reason the action asks for, when it asks for one. */
  motivo?: {
    etiqueta: string;
    placeholder?: string;
    requerido?: boolean;
  };
  /** The confirm button. */
  confirmar: {
    etiqueta: string;
    /** Why the action cannot be executed yet. */
    deshabilitado?: boolean;
    /** Whether the action is running. */
    enCurso?: boolean;
  };
  /** Called when the operator confirms. */
  onConfirmar?: (motivo: string) => void;
  /**
   * The message of a failure of the last attempt.
   *
   * It is the VERBATIM prose of the backend: the interface never translates a
   * public message and never invents one.
   */
  error?: string;
  /**
   * The failure of the field that carries the reason.
   *
   * It arrives from the `422` of the backend through the frozen channel
   * `error.field_errors[]` (`FREEZE-ENV-1.0.0` §4.2).
   */
  errorDeCampo?: string;
  /** Additional audited evidence fields required by this concrete command. */
  contenido?: ReactNode;
}

/**
 * ConfirmacionIrreversible - the S-10 state of a sensitive action.
 *
 * It names the effect, captures the reason when the action asks for one and
 * NEVER shows a bare "¿Está seguro?". It is a plain labelled control and NOT
 * a `GenericForm`: the wire schema of the action does not exist yet, so a
 * Zod mirror would be an invented contract. API-04 binds it to the real
 * payload.
 *
 * The reason is a PRESENTATION requirement, not a business rule: the effect
 * and the reason are what the operator must read before acting.
 */
export function ConfirmacionIrreversible({
  abierto,
  onAbiertoChange,
  titulo,
  efecto,
  motivo,
  confirmar,
  onConfirmar,
  error,
  errorDeCampo,
  contenido,
}: ConfirmacionIrreversibleProps) {
  const idMotivo = useId();
  const [valorMotivo, setValorMotivo] = useState("");
  const [tocado, setTocado] = useState(false);

  const faltaMotivo = Boolean(motivo?.requerido) && valorMotivo.trim() === "";
  const bloqueado = confirmar.deshabilitado || confirmar.enCurso || faltaMotivo;
  const idErrorServidor = `${idMotivo}-error-servidor`;
  const describedBy =
    [
      tocado && faltaMotivo ? `${idMotivo}-error` : null,
      errorDeCampo ? idErrorServidor : null,
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <AlertDialog open={abierto} onOpenChange={onAbiertoChange}>
      <AlertDialogContent className="sm:max-w-lg">
        <AlertDialogHeader>
          <AlertDialogTitle>{titulo}</AlertDialogTitle>
          <AlertDialogDescription>{efecto}</AlertDialogDescription>
        </AlertDialogHeader>

        {contenido}

        {motivo ? (
          <div className="flex flex-col gap-2">
            <FormField
              id={idMotivo}
              label={motivo.etiqueta}
              required={motivo.requerido}
              error={
                tocado && faltaMotivo
                  ? "Escribe el motivo: queda registrado en la auditoría."
                  : undefined
              }
            >
              {(control) => (
                <Textarea
                  {...control}
                  value={valorMotivo}
                  placeholder={motivo.placeholder}
                  rows={3}
                  aria-required={motivo.requerido ? true : undefined}
                  aria-describedby={describedBy}
                  onChange={(evento) => setValorMotivo(evento.target.value)}
                  onBlur={() => setTocado(true)}
                />
              )}
            </FormField>
            {errorDeCampo ? (
              <p id={idErrorServidor} className="text-caption text-destructive">
                {errorDeCampo}
              </p>
            ) : null}
          </div>
        ) : null}

        {confirmar.deshabilitado ? (
          <p className="text-sm leading-relaxed text-muted-foreground">
            La acción todavía no está conectada: el endpoint que la ejecuta
            todavía no está registrado en el backend.
          </p>
        ) : null}

        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <AlertDialogFooter>
          <AlertDialogCancel className="min-h-11">Cancelar</AlertDialogCancel>
          <AlertDialogAction
            className="min-h-11"
            disabled={bloqueado}
            onClick={(evento) => {
              if (bloqueado) {
                evento.preventDefault();
                return;
              }
              onConfirmar?.(valorMotivo.trim());
            }}
          >
            {confirmar.enCurso ? "Ejecutando…" : confirmar.etiqueta}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
