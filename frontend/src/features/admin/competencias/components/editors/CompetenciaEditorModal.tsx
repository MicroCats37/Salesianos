"use client";

import type { ReactNode } from "react";
import { GenericModal } from "@/components/genericModal/GenericModal";

export interface CompetenciaEditorModalProps {
  /** Whether the modal is open. */
  open: boolean;
  /** The state of the modal. */
  onOpenChange: (open: boolean) => void;
  /** Title of the modal. */
  titulo: string;
  /** Explanation of what the editor does. */
  descripcion?: string;
  /** The editor. */
  children: ReactNode;
}

/**
 * CompetenciaEditorModal — the modal that hosts ONE editor of the module.
 *
 * The editor keeps its own presentation: the modal only frames it, closes
 * with the ESC key and traps the focus like the rest of the dialogs of the
 * application.
 */
export function CompetenciaEditorModal({
  open,
  onOpenChange,
  titulo,
  descripcion,
  children,
}: CompetenciaEditorModalProps) {
  return (
    <GenericModal open={open} onOpenChange={onOpenChange}>
      <GenericModal.Content>
        <GenericModal.Header title={titulo} description={descripcion} />
        <GenericModal.Body>{children}</GenericModal.Body>
      </GenericModal.Content>
    </GenericModal>
  );
}
