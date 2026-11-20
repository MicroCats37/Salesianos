"use client";

import { useState } from "react";
import { ScanLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * ConsolaEscaner - the console of a point of control.
 *
 * It is the SAME console for the entry of the party (`ADM-16`) and for the
 * pickup of the store (`ADM-20`): one credential field, one check and one
 * confirm, and the two flows differ in the subject they read.
 *
 * The KEYBOARD path is the primary one and it always works: the code is
 * typed, the field is a real `<label>`ed input and the check is a real
 * button. The camera is an accelerator, never the only way in, so a device
 * without a camera — or an operator with a reader that is not connected — is
 * not blocked.
 *
 * While the check is in flight the button says what it is doing and the
 * field is locked: the interface never invents a remaining time (`SH-03`
 * S-08).
 */
export function ConsolaEscaner({
  etiquetaCodigo = "Código de la credencial",
  ayuda,
  onComprobar,
  ocupado = false,
  disabled = false,
}: {
  /** The name of the field, in the words of the operation. */
  etiquetaCodigo?: string;
  /** The hint under the field. */
  ayuda?: string;
  /** The check. It is OPTIONAL: without it the console says why. */
  onComprobar?: (codigo: string) => void;
  /** Whether a check is in flight. */
  ocupado?: boolean;
  /** Whether the console is locked. */
  disabled?: boolean;
}) {
  const [codigo, setCodigo] = useState("");

  const ayudaId = "consola-escaner-ayuda";
  const sinServicio =
    "El servicio de validación todavía no está conectado en el backend: el código se puede escribir, pero la comprobación no sale de este dispositivo.";

  return (
    <form
      className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-4"
      onSubmit={(evento) => {
        evento.preventDefault();
        if (!onComprobar || ocupado || disabled) return;
        onComprobar(codigo.trim());
      }}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="codigo-credencial">{etiquetaCodigo}</Label>
        <Input
          id="codigo-credencial"
          name="codigo"
          value={codigo}
          onChange={(evento) => setCodigo(evento.target.value)}
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          disabled={ocupado || disabled}
          aria-describedby={ayudaId}
          className="min-h-11"
        />
        <p id={ayudaId} className="text-caption text-muted-foreground">
          {ayuda ?? sinServicio}
        </p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Button
          type="submit"
          disabled={!onComprobar || ocupado || disabled || codigo.trim() === ""}
          className="min-h-11 sm:w-auto"
        >
          <ScanLine className="size-4" aria-hidden="true" />
          {ocupado ? "Comprobando…" : "Comprobar"}
        </Button>
        <p className="text-caption text-muted-foreground">
          Comprobar no consume: solo muestra lo que el servidor responde. El
          consumo es una confirmación aparte.
        </p>
      </div>
    </form>
  );
}
