"use client";

import { useState } from "react";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemHeader,
  ItemTitle,
} from "@/components/ui/item";
import { Button } from "@/components/ui/button";
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
 * names the effect (`SH-03` S-10).
 */
export function ListaBeneficiarios({
  beneficiarios,
  revocar,
  className,
}: ListaBeneficiariosProps) {
  const [aRevocar, setARevocar] = useState<BeneficiarioPase | null>(null);

  if (beneficiarios.length === 0) {
    return (
      <p className={className}>
        Todavía no hay ninguna entrada asignada. Eliges quién usa cada pase
        con el formulario de arriba.
      </p>
    );
  }

  return (
    <div className={className}>
      <ItemGroup className="gap-3">
        {beneficiarios.map((beneficiario) => (
          <Item key={beneficiario.id} variant="outline" role="listitem">
            <ItemHeader>
              <ItemContent>
                <ItemTitle className="text-foreground">
                  {`${beneficiario.persona_nombres} ${beneficiario.persona_apellidos}`.trim()}
                </ItemTitle>
                <ItemDescription>
                  {`${beneficiario.persona_tipo_documento} ${beneficiario.persona_numero_documento}`}
                </ItemDescription>
              </ItemContent>

              <span className="text-xs font-semibold text-foreground">
                {beneficiario.estado_etiqueta}
              </span>
            </ItemHeader>

            {beneficiario.revocado_en ? (
              <p className="text-caption text-muted-foreground">
                {`Revocada el ${beneficiario.revocado_en}.`}
              </p>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="min-h-11"
                onClick={() => setARevocar(beneficiario)}
              >
                Revocar la entrada
              </Button>
            )}
          </Item>
        ))}
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
