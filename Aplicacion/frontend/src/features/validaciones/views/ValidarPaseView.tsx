import { ScanLine } from "lucide-react";
import Link from "next/link";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import { ConfirmacionValidacion } from "../components/ConfirmacionValidacion";
import { ConsolaEscaner } from "../components/ConsolaEscaner";
import { VistaPreviaValidacion } from "../components/VistaPreviaValidacion";
import type {
  EstadoVistaValidaciones,
  ResultadoValidacion,
  VistaPreviaValidacion as VistaPrevia,
} from "../types/validacion.types";

/**
 * ValidarPaseView - `ADM-16`, the entrance control of the party.
 *
 * This is the surface of the person who checks a pass at the door, and it
 * answers ONE question: does this right let this person in?
 *
 * The flow has THREE states and they are never merged: the check (which does
 * not consume), the preview (what the server answered) and the confirmation
 * (which consumes). Reading a code is NOT a consumption (`SH-03` ADM-16).
 */
export function ValidarPaseView({
  estado = "sin-datos",
  vistaPrevia,
  resultado,
  onComprobar,
  onConfirmar,
  ocupado = false,
}: {
  estado?: EstadoVistaValidaciones;
  vistaPrevia?: VistaPrevia;
  resultado?: ResultadoValidacion;
  /** The check of a code. */
  onComprobar?: (codigo: string) => void;
  /** The confirmation of the validation. */
  onConfirmar?: () => void;
  /** Whether an operation is in flight. */
  ocupado?: boolean;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-16"
        title="Controlar el ingreso a la fiesta"
        description="La validación de entradas: se comprueba el pase de una persona y se registra el resultado del acceso en el punto de control."
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.validaciones}>
              Ver la auditoría de accesos
            </Link>
          </Button>
        }
      />

      <AdminNotice title="El código es una credencial">
        El código que se escanea es una credencial en sí mismo: no se publica en
        la lista, no se copia en un registro y no se enseña en pantalla para que
        alguien más lo use.
      </AdminNotice>

      {estado === "sin-permiso" ? (
        <ShellPermissionDenied title="No tienes permiso para validar entradas" />
      ) : estado === "error" ? (
        <ShellErrorState
          title="No pudimos comprobar la entrada"
          description="El servidor no respondió a la comprobación. Puedes volver a intentarlo; si el problema continúa, revisa el punto de control."
          accion={{ label: "Reintentar" }}
        />
      ) : (
        <>
          <AdminPanel
            title="Comprobación"
            description="Escribe o escanea el código de la credencial para saber si el ingreso es posible."
          >
            <ConsolaEscaner
              etiquetaCodigo="Código de la entrada"
              ayuda="La comprobación no consume la entrada: solo dice lo que responde el servidor."
              onComprobar={onComprobar}
              ocupado={ocupado}
              disabled={estado === "sin-datos"}
            />
          </AdminPanel>

          {vistaPrevia ? (
            <AdminPanel
              title="Vista previa"
              description="Lo que el servidor respondió de la credencial, antes de consumirla."
            >
              <VistaPreviaValidacion vistaPrevia={vistaPrevia} />
            </AdminPanel>
          ) : null}

          <AdminPanel
            title="Confirmación"
            description="El registro del acceso, con tu nombre, el punto de control y el instante."
          >
            <ConfirmacionValidacion
              vistaPrevia={vistaPrevia}
              resultado={resultado}
              onConfirmar={onConfirmar}
              ocupado={ocupado}
              etiquetaAccion="Confirmar el ingreso"
            />
          </AdminPanel>

          {estado === "sin-datos" ? (
            <AdminEmptyState
              icon={ScanLine}
              title="El servicio de validación todavía no está conectado"
              description="El módulo de validaciones no existe en el backend, así que ninguna comprobación sale de este dispositivo. Cuando el servicio esté conectado, esta consola comprobará la credencial, mostrará su vista previa y sólo después permitirá confirmar el acceso."
            />
          ) : null}
        </>
      )}
    </div>
  );
}
