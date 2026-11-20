import { GitBranch } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-12 - the bracket of a competition.
 *
 * The bracket is one column per round and one cell per encounter. It is the
 * densest screen of the area and it is read horizontally: the cells of a
 * round are lined up and the winner is carried to the next one.
 */
export function AdminCuadroView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-12"
        title="Operar el cuadro de encuentros"
        description="El cuadro de la competencia: una columna por ronda, una celda por encuentro, con el ganador que avanza a la siguiente."
        meta={[{ etiqueta: "Competencia", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.competencias}>
              Volver a las competencias
            </Link>
          </Button>
        }
      />

      <AdminNotice title="El servidor manda en el cuadro">
        Programar un encuentro, configurar un bye, enlazar, registrar un
        resultado o confirmar un avance son acciones con motivo auditado y
        bloqueo optimista: si otra persona cambió la misma versión, el
        servidor rechaza el cambio y nada se escribe.
      </AdminNotice>

      <AdminPanel
        title="Cuadro"
        description="Las rondas del cuadro y los encuentros de cada una."
      >
        <AdminEmptyState
          icon={GitBranch}
          title="Todavía no hay un cuadro que mostrar"
          description="El cuadro se construye sobre las rondas y los encuentros de la competencia. Cuando la integración esté disponible, aquí se pintará una columna por ronda con una celda por encuentro, su marcador y el bloque de acciones del encuentro."
        />
      </AdminPanel>
    </div>
  );
}
