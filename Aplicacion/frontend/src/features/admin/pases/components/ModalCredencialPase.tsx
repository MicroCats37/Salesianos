"use client";

import { Copy, KeyRound, Ticket } from "lucide-react";
import { useState } from "react";
import { GenericModal } from "@/components/genericModal";
import { Button } from "@/components/ui/button";
import { useEmitirCredencial } from "../hooks/useAdminPases";
import { AvisoFalloPase } from "./AvisoFalloPase";

export interface ModalCredencialPaseProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal opens or closes. */
  onOpenChange: (open: boolean) => void;
  /** The RIGHT that receives the credential. */
  derechoId: string | null;
  /** The person who receives the credential. */
  persona?: string;
  /** The pass of the right. */
  pase?: string;
}

/**
 * ModalCredencialPase - the ONE-SHOT credential of the door.
 *
 * ## THE SECRET
 *
 * The code of the ticket is published ONCE. It is shown here, it can be
 * copied, and it is DISCARDED when the dialog closes: it never enters the
 * query cache, it never enters the mutation cache and it never reaches a
 * store (`F6`).
 *
 * ## THE DOCUMENT
 *
 * The credential is the credential: the document declares WHO, never WHAT the
 * person may do. The door scans a TICKET, never a document (`R5`).
 */
export function ModalCredencialPase({
  open,
  onOpenChange,
  derechoId,
  persona,
  pase,
}: ModalCredencialPaseProps) {
  const emision = useEmitirCredencial();
  const [copiado, setCopiado] = useState(false);

  function cerrar() {
    emision.descartar();
    setCopiado(false);
    onOpenChange(false);
  }

  async function copiar() {
    const codigo = emision.credencial?.codigo;

    if (!codigo) {
      return;
    }

    try {
      await navigator.clipboard.writeText(codigo);
      setCopiado(true);
    } catch {
      setCopiado(false);
    }
  }

  const credencial = emision.credencial;

  return (
    <GenericModal open={open} onOpenChange={cerrar}>
      <GenericModal.Content>
        <GenericModal.Header
          title="Emitir la credencial de puerta"
          description="La credencial habilita el ingreso y se entrega una sola vez. Cópiala antes de cerrar: después no vuelve a estar disponible."
        />

        <GenericModal.Body className="flex flex-col gap-4">
          {/*
            The ANNOUNCEMENT of the credential.

            The region is ALWAYS mounted: a live region only announces a
            change of its OWN content, so a region that appeared together
            with the secret would stay silent. It names the code because the
            operator has to READ it and deliver it - and it says so once,
            politely, next to the copy confirmation.
          */}
          <p aria-live="polite" className="sr-only">
            {credencial
              ? `Credencial emitida: ${credencial.codigo}. Cópiala antes de cerrar.`
              : ""}
          </p>

          {emision.fallo ? <AvisoFalloPase fallo={emision.fallo} /> : null}

          {persona || pase ? (
            <p className="text-sm text-foreground">
              {persona}
              {pase ? ` — ${pase}` : ""}
            </p>
          ) : null}

          {credencial ? (
            <section
              aria-labelledby="credencial-codigo-titulo"
              className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-border p-4"
            >
              <h3
                id="credencial-codigo-titulo"
                className="text-sm font-semibold text-foreground"
              >
                La credencial
              </h3>

              <p className="text-caption text-muted-foreground">
                Tipo de derecho: {credencial.tipo_derecho}. Operación:{" "}
                {credencial.operacion}.
              </p>

              <code className="block select-all break-all rounded-[var(--radius-sm)] bg-surface-recessed px-3 py-2 font-mono text-base tracking-wide text-foreground">
                {credencial.codigo}
              </code>

              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="outline" onClick={copiar}>
                  <Copy className="size-4" aria-hidden="true" />
                  Copiar la credencial
                </Button>
                <p
                  aria-live="polite"
                  className="text-caption text-muted-foreground"
                >
                  {copiado ? "Credencial copiada." : ""}
                </p>
              </div>

              <p className="text-caption text-muted-foreground">
                Esta credencial es una credencial en sí misma: entrégala a la
                persona y no la compartas.
              </p>
            </section>
          ) : (
            <section className="flex flex-col gap-3">
              <p className="text-sm text-foreground">
                Todavía no hay ninguna credencial emitida. Al emitirla, el
                servidor genera el código y lo devuelve una sola vez.
              </p>

              {derechoId ? (
                <Button
                  type="button"
                  onClick={() => {
                    void emision.emitir(derechoId);
                  }}
                  disabled={emision.estado === "emitiendo"}
                >
                  <Ticket className="size-4" aria-hidden="true" />
                  {emision.estado === "emitiendo"
                    ? "Emitiendo..."
                    : "Emitir la credencial"}
                </Button>
              ) : (
                <p className="text-caption text-muted-foreground">
                  <KeyRound className="mr-1 inline size-4" aria-hidden="true" />
                  La credencial se emite contra el DERECHO de la persona. Esta
                  cortesía no tiene un derecho asociado, así que no hay nada que
                  emitir.
                </p>
              )}
            </section>
          )}
        </GenericModal.Body>

        <GenericModal.Footer>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={cerrar}>
              Cerrar
            </Button>
          </div>
        </GenericModal.Footer>

        <GenericModal.CloseX />
      </GenericModal.Content>
    </GenericModal>
  );
}
