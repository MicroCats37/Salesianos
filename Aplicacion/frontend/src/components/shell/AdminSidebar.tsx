import {
  type AdminDestino,
  type AdminGrupo,
} from "@/features/admin/utils/admin.secciones";
import { AppSidebar } from "./AppSidebar";

export interface AdminSidebarProps {
  resumen: AdminDestino;
  grupos: AdminGrupo[];
  /** Label of the signed-in account, shown in the footer. */
  usuario?: string;
  /** The tier of the account, shown in the footer. */
  nivel?: string;
  /** Whether the account holds the break-glass tier. */
  superusuario?: boolean;
}

/**
 * AdminSidebar - the navigation of the administration area.
 *
 * It is the shared navigation of the authenticated product (`AppSidebar`)
 * with the groups of administration: the destinations of the responsible
 * are at the top and the sections the backend opened are below.
 *
 * The destinations arrive as a prop, already filtered by the capability
 * session the server read. The client never decides what an administrator
 * may open: hiding an entry is a courtesy and the 403 of the backend is the
 * control.
 */
export function AdminSidebar({
  resumen,
  grupos,
  usuario,
  nivel,
  superusuario = false,
}: AdminSidebarProps) {
  return (
    <AppSidebar
      resumen={resumen}
      grupos={grupos}
      usuario={usuario}
      nivel={nivel}
      superusuario={superusuario}
      area="Panel de control"
    />
  );
}
