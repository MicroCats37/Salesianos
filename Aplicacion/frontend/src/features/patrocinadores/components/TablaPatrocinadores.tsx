import { Eye, EyeOff, Handshake } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
} from "@/features/admin/components";
import { LogoPatrocinador } from "./LogoPatrocinador";
import type { Patrocinador } from "../types/patrocinador.types";

/**
 * TablaPatrocinadores - the sponsors of the edition (`ADM-21`).
 *
 * The row carries the logo, the name, the identifier, the edition, the
 * visibility and the number of pieces. It carries NO monetary field: a
 * sponsor has no amount, no contribution and no commission
 * (`GOV-02-RB-08b`).
 */
export function TablaPatrocinadores({
  patrocinadores,
}: {
  patrocinadores: Patrocinador[];
}) {
  if (patrocinadores.length === 0) {
    return (
      <AdminEmptyState
        icon={Handshake}
        title="Todavía no hay patrocinadores en la edición"
        description="El servicio de patrocinadores todavía no está disponible en el backend, así que aquí no se dibuja ninguna ficha. Cuando lo esté, se listarán con su logo, con su galería ordenada y con su visibilidad."
      />
    );
  }

  return (
    <AdminDataTable
      caption="Patrocinadores de la edición"
      columns={[
        { key: "logo", label: "Logo" },
        { key: "patrocinador", label: "Patrocinador" },
        { key: "slug", label: "Identificador", identificador: true },
        { key: "edicion", label: "Edición" },
        { key: "visibilidad", label: "Visibilidad" },
        { key: "piezas", label: "Piezas", numerico: true },
      ]}
      filas={patrocinadores.map((patrocinador) => ({
        cells: {
          logo: (
            <LogoPatrocinador
              logo={patrocinador.logo}
              nombre={patrocinador.nombre}
            />
          ),
          patrocinador: (
            <span className="font-medium text-foreground">
              {patrocinador.nombre}
            </span>
          ),
          slug: (
            <span className="font-mono text-xs text-muted-foreground">
              {patrocinador.slug}
            </span>
          ),
          edicion: (
            <span className="text-muted-foreground">
              {patrocinador.edicion_nombre}
            </span>
          ),
          visibilidad: (
            <span className="inline-flex items-center gap-1.5 text-sm text-foreground">
              {patrocinador.visible ? (
                <Eye className="size-3.5 text-success" aria-hidden="true" />
              ) : (
                <EyeOff
                  className="size-3.5 text-foreground-muted"
                  aria-hidden="true"
                />
              )}
              {patrocinador.visible ? "Visible" : "Oculto"}
            </span>
          ),
          piezas: String(patrocinador.imagenes.length),
        },
      }))}
    />
  );
}
