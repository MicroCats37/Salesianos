"use client";

import { Ticket } from "lucide-react";
import { useState } from "react";
import {
  ModalCompraParaCliente,
  useComprarPaseCliente,
} from "@/features/admin/asistido";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { useCatalogoPases } from "@/features/pases/hooks/useCatalogoPases";

/**
 * ADM-15 - the party passes and the courtesy passes.
 *
 * A pass is a nominative right: it belongs to a person, it can be revoked,
 * and it carries its own payment evidence. The revenue of the passes is
 * deliberately kept apart from the sport metrics of the edition.
 *
 * ## The assisted purchase
 *
 * Every row of the catalogue exposes "Comprar para cliente": the operator
 * sells a pass to a walk-in customer who has no account. The command declares
 * the CIVIL identity of the client and the backend makes the CLIENT the owner
 * of the purchase and of the batch, while the administrator stays the actor
 * of the operation.
 */
export function AdminPasesView() {
  const [paseParaCliente, setPaseParaCliente] = useState<{
    id: string;
    nombre: string;
    monto: number;
    moneda: string;
  } | null>(null);
  const catalogo = useCatalogoPases();
  const comprarParaCliente = useComprarPaseCliente();

  const pases = catalogo.data?.pases ?? [];

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-15"
        title="Gestionar pases de fiesta y cortesías"
        description="Los pases de la fiesta y las cortesías de la organización, con su titular, su estado y su evidencia de pago."
      />

      <AdminNotice title="Ingreso separado del deporte">
        El ingreso de los pases no se mezcla con las métricas deportivas de la
        edición: una venta de pases no es una inscripción y no ocupa cupo.
      </AdminNotice>

      <AdminPanel
        title="Catálogo de pases"
        description="Los pases a la venta de la edición, con su precio vigente y el acceso para venderlos a un cliente."
      >
        {catalogo.isPending ? (
          <output className="block py-10 text-center text-sm text-muted-foreground">
            Cargando el catálogo de pases...
          </output>
        ) : null}
        {catalogo.isError ? (
          <div
            role="alert"
            className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
          >
            No pudimos cargar el catálogo de pases. Inténtalo de nuevo en unos
            segundos.
          </div>
        ) : null}
        {catalogo.isSuccess ? (
          <AdminDataTable
            caption="Pases a la venta de la edición"
            columns={[
              { key: "pase", label: "Pase" },
              { key: "estado", label: "Estado" },
              { key: "precio", label: "Precio vigente", numerico: true },
              { key: "acciones", label: "Acciones" },
            ]}
            filas={pases.map((pase) => ({
              cells: {
                pase: (
                  <div className="min-w-48">
                    <p className="truncate font-medium text-foreground">
                      {pase.nombre}
                    </p>
                    <p className="text-caption text-muted-foreground">
                      {pase.descripcion}
                    </p>
                  </div>
                ),
                estado:
                  pase.estado === "VIGENTE" ? "A la venta" : "No a la venta",
                precio: new Intl.NumberFormat("es-ES", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }).format(pase.precio.monto),
                acciones: (
                  <button
                    type="button"
                    className="inline-flex min-h-9 items-center gap-2 whitespace-nowrap rounded-[var(--radius-md)] border border-input bg-transparent px-3 text-sm outline-none hover:bg-accent focus-visible:ring-3 focus-visible:ring-ring/50"
                    onClick={() =>
                      setPaseParaCliente({
                        id: pase.id,
                        nombre: pase.nombre,
                        monto: pase.precio.monto,
                        moneda: pase.precio.moneda,
                      })
                    }
                  >
                    <Ticket className="size-3.5" aria-hidden="true" />
                    Comprar para cliente
                  </button>
                ),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={Ticket}
                title="Todavía no hay pases cargados"
                description="Los pases se leen del catálogo de la edición. Cuando la edición tenga pases a la venta, aquí se listarán con su precio vigente y la acción de venderlos a un cliente."
              />
            }
          />
        ) : null}
      </AdminPanel>

      {paseParaCliente ? (
        <ModalCompraParaCliente
          open
          onOpenChange={(abierto) => {
            if (!abierto) setPaseParaCliente(null);
          }}
          modo="PASE"
          concepto={paseParaCliente.nombre}
          itemId={paseParaCliente.id}
          precioUnitario={new Intl.NumberFormat("es-ES", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }).format(paseParaCliente.monto)}
          moneda={paseParaCliente.moneda}
          comprando={comprarParaCliente.isPending}
          onComprar={async (datos) => {
            await comprarParaCliente.mutateAsync({
              pase_id: paseParaCliente.id,
              cantidad: datos.cantidad,
              cliente: {
                tipo_documento: datos.tipo_documento,
                numero_documento: datos.numero_documento,
                nombres: datos.nombres,
                apellidos: datos.apellidos,
                contacto_email: datos.contacto_email,
              },
              evidencia: {
                canal: datos.canal,
                referencia: datos.referencia,
                motivo: datos.motivo,
              },
            });
            setPaseParaCliente(null);
          }}
        />
      ) : null}
    </div>
  );
}
