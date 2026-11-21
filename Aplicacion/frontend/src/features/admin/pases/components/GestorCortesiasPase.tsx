"use client";

import { useState } from "react";
import { AdminPanel } from "@/features/admin/components/AdminPanel";
import { useEstadoCortesias } from "../hooks/useAdminPases";
import type { AdminCortesiaListaItem } from "../schemas/admin.pase.schema";
import { ModalCortesiaPase } from "./ModalCortesiaPase";
import { ModalCredencialPase } from "./ModalCredencialPase";
import { ModalRevocarCortesia } from "./ModalRevocarCortesia";
import { PanelCortesias } from "./PanelCortesias";

/**
 * GestorCortesiasPase - the block of the administrative courtesies.
 *
 * It is SELF-CONTAINED: the read, the grant, the revocation and the issue of
 * the credential live together, so the composition in the route is a single
 * import and nothing of the area leaks into the view that hosts it.
 */
export function GestorCortesiasPase() {
  const [registroAbierto, setRegistroAbierto] = useState(false);
  const [aRevocar, setARevocar] = useState<AdminCortesiaListaItem | null>(null);
  const [aEmitir, setAEmitir] = useState<AdminCortesiaListaItem | null>(null);

  const estado = useEstadoCortesias();

  return (
    <AdminPanel
      title="Cortesías"
      description="Las entradas que la organización otorga sin cobro: el acta, el motivo, el responsable y el estado de cada una."
    >
      <PanelCortesias
        estado={estado}
        onRegistrar={() => setRegistroAbierto(true)}
        onRevocar={(cortesia) => setARevocar(cortesia)}
        onEmitirCredencial={(cortesia) => setAEmitir(cortesia)}
      />

      <ModalCortesiaPase
        open={registroAbierto}
        onOpenChange={setRegistroAbierto}
      />

      <ModalRevocarCortesia
        open={Boolean(aRevocar)}
        onOpenChange={(abierto) => {
          if (!abierto) {
            setARevocar(null);
          }
        }}
        cortesia={aRevocar}
      />

      {/*
        The credential dialog is MOUNTED only while it is needed: unmounting
        it discards the secret of the ticket, which must never outlive the
        moment it was shown (`F6`).
      */}
      {aEmitir ? (
        <ModalCredencialPase
          open
          onOpenChange={() => setAEmitir(null)}
          derechoId={aEmitir.derecho_id ?? null}
          persona={aEmitir.persona_nombres}
          pase={aEmitir.pase_nombre}
        />
      ) : null}
    </AdminPanel>
  );
}
