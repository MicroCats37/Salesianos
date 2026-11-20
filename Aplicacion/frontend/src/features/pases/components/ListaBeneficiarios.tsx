"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemHeader,
  ItemTitle,
} from "@/components/ui/item";
import { cn } from "@/lib/utils";
import type { BeneficiarioPase } from "../types/pase.types";
import { DialogoRevocar } from "./DialogoRevocar";

export interface ListaBeneficiariosProps {
  /** The rights granted in the batch. */
  beneficiarios: BeneficiarioPase[];
  /** The revocation. It does not exist yet. */
  revocar?: (beneficiario: BeneficiarioPase, motivo: string) => Promise<void>;
  className?: string;
}

/**
 * ListaBeneficiarios - the persons that hold an entry of the batch.
 *
 * The list shows the state the backend published, never a recomputation, and
 * it never exposes a machine code: the label travels with the fact
 * (`estado_etiqueta`).
 *
 * The revocation is IRREVERSIBLE, so it goes through its own dialog that
 * names the effect (`SH-03` S-10) and the button that opens it says so
 * before it is pressed.
 */
export function ListaBeneficiarios({
  beneficiarios,
  revocar,
  className,
}: ListaBeneficiariosProps) {
  const [aRevocar, setARevocar] = useState<BeneficiarioPase | null>(null);

  if (beneficiarios.length === 0) {
    return (
      <p
        className={cn(
          "rounded-[var(--radius-lg)] border border-dashed border-border bg-surface-recessed p-4 text-caption text-muted-foreground",
          className,
        )}
      >
        Todavía no hay ninguna entrada asignada. Eliges quién usa cada pase con
        el formulario de arriba.
      </p>
    );
  }

  return (
    <div className={className}>
      <ItemGroup className="gap-3">
        {beneficiarios.map((beneficiario) => {
          const revocado = Boolean(beneficiario.revocado_en);

          return (
            <Item
              key={beneficiario.id}
              variant="outline"
              asChild
              className="rounded-[var(--radius-xl)] bg-surface-raised p-4"
            >
              <li>
                <ItemHeader>
                  <ItemContent>
                    <ItemTitle className="text-base font-bold text-foreground">
                      {`${beneficiario.persona_nombres} ${beneficiario.persona_apellidos}`.trim()}
                    </ItemTitle>
                    <ItemDescription>
                      {`${beneficiario.persona_tipo_documento} ${beneficiario.persona_numero_documento}`}
                    </ItemDescription>
                  </ItemContent>

                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0",
                      revocado
                        ? "border-destructive/45 bg-destructive/12 text-destructive"
                        : "border-success/45 bg-success/12 text-success",
                    )}
                  >
                    {beneficiario.estado_etiqueta}
                  </Badge>
                </ItemHeader>

                {revocado ? (
                  <p className="text-caption text-destructive">
                    {`Revocada el ${beneficiario.revocado_en}.`}
                  </p>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="min-h-11 text-destructive hover:text-destructive"
                    onClick={() => setARevocar(beneficiario)}
                  >
                    Revocar la entrada
                  </Button>
                )}
              </li>
            </Item>
          );
        })}
      </ItemGroup>

      <DialogoRevocar
        beneficiario={aRevocar}
        abierto={aRevocar !== null}
        onOpenChange={(abierto) => {
          if (!abierto) setARevocar(null);
        }}
        revocar={revocar}
      />
    </div>
  );
}
