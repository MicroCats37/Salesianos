import { UserCog } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-04 - the accounts of the platform.
 *
 * The section publishes WHO holds each tier, and it does not manage
 * accounts: promoting, degrading, activating or resetting a password is
 * not part of this surface. The tier is shown so an account administrator
 * can see who carries the break-glass level.
 */
export function AdminUsuariosView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-04"
        title="Gestionar cuentas y grupos"
        description="Las cuentas registradas en la plataforma, con su nivel de acceso dentro del evento y su último acceso."
      />

      <AdminNotice title="Esta sección no gestiona cuentas">
        No promueve, no degrada, no activa ni desactiva cuentas y no reinicia
        contraseñas. Publica el nivel de cada cuenta para que se vea quién lo
        tiene; la gestión de cuentas pertenece a otra superficie.
      </AdminNotice>

      <AdminPanel
        title="Cuentas"
        description="Usuarios registrados, con su identidad y su nivel dentro del evento."
      >
        <AdminDataTable
          caption="Cuentas registradas"
          columns={[
            { key: "usuario", label: "Usuario", identificador: true },
            { key: "nombre", label: "Nombre" },
            { key: "correo", label: "Correo" },
            { key: "documento", label: "Documento", identificador: true },
            { key: "nivel", label: "Nivel" },
            { key: "estado", label: "Estado" },
            { key: "ultimo", label: "Último acceso", numerico: true },
            { key: "creado", label: "Creado", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={UserCog}
              title="Todavía no hay cuentas cargadas"
              description="La tabla de cuentas se lee del servicio de administración. Cuando la integración esté disponible, aquí se listarán las cuentas con su nivel y su último acceso, con su búsqueda y sus filtros."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
