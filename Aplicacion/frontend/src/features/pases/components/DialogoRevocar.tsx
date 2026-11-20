"use client";

import { TriangleAlert } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { BeneficiarioPase } from "../types/pase.types";

export interface DialogoRevocarProps {
  /** The right that is about to be revoked. */
  beneficiario: BeneficiarioPase | null;
  /** Whether the dialog is open. */
  abierto: boolean;
  /** The change of the open state. */
  onOpenChange: (abierto: boolean) => void;
  /** The revocation itself. It does not exist yet. */
  revocar?: (beneficiario: BeneficiarioPase, motivo: string) => Promise<void>;
}

/**
 * DialogoRevocar - the irreversible confirmation of a revocation.
 *
 * `SH-03` S-10: the dialog NAMES the concrete effect. It does not say "are
 * you sure?" and it does not hide that the revocation is permanent and
 * audited (`FR-05` §2.3).
 *
 * The policy of the reassignment is still OPEN (`PD-02`), and the dialog says
 * so instead of promising something the backend has not decided.
 *
 * The confirming action is painted as DESTRUCTIVE: the word of the button
 * already says what it does, and the colour says it before it is pressed.
 */
export function DialogoRevocar({
  beneficiario,
  abierto,
  onOpenChange,
  revocar,
}: DialogoRevocarProps) {
  const nombre = beneficiario
    ? `${beneficiario.persona_nombres} ${beneficiario.persona_apellidos}`.trim()
    : "";

  return (
    <AlertDialog open={abierto} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogMedia className="bg-destructive/10 text-destructive">
            <TriangleAlert className="size-6" aria-hidden="true" />
          </AlertDialogMedia>

          <AlertDialogTitle>{`Revocar la entrada de ${nombre}`}</AlertDialogTitle>
          <AlertDialogDescription>
            Revocar la entrada la deja sin efecto y queda registrada en la
            auditoría. No genera devolución ni devuelve el pase al lote, y la
            política de reasignación todavía no está acordada: el pase puede
            quedar sin dueño.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel className="min-h-11">
            Mantener la entrada
          </AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            className="min-h-11"
            disabled={!revocar || !beneficiario}
            onClick={() => {
              if (!revocar || !beneficiario) return;
              void revocar(beneficiario, "");
            }}
          >
            Revocar la entrada
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
