"use client";

import { LoaderCircle, PackageCheck } from "lucide-react";
import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import {
  useConfirmarEntrega,
  useEntregas,
} from "@/features/marketplace/hooks/useInventarioMarketplace";
import { RUTAS } from "@/lib/routes";

const formatoMoneda = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
});

const formatoFecha = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** ADM-20 - the operational record of marketplace handovers. */
export function AdminEntregasView({
  embedded = false,
}: {
  embedded?: boolean;
}) {
  const [pedidoPorConfirmar, setPedidoPorConfirmar] = useState<string | null>(
    null,
  );
  const entregas = useEntregas();
  const confirmarEntrega = useConfirmarEntrega();

  const confirmar = async () => {
    if (!pedidoPorConfirmar) return;
    await confirmarEntrega.mutateAsync(pedidoPorConfirmar);
    setPedidoPorConfirmar(null);
  };

  return (
    <div
      id={embedded ? "recogidas" : undefined}
      className="flex flex-col gap-6"
    >
      {!embedded ? (
        <>
          <AdminPageHeader
            pageId="ADM-20"
            title="Validar las recogidas"
            description="Los pedidos pagados que todavía esperan su entrega física."
          />

          <AdminSubnav
            ariaLabel="Secciones de la tienda"
            items={[
              {
                href: RUTAS.administracion.marketplace,
                label: "Tienda",
                description: "Catálogo y precios",
              },
              {
                href: RUTAS.administracion.marketplaceInventario,
                label: "Inventario",
                description: "Movimientos de stock",
              },
            ]}
          />
        </>
      ) : null}

      <AdminPanel
        title="Recogidas por confirmar"
        description="La confirmación registra un acta en el servidor; no modifica el precio ni el pago."
      >
        {entregas.isPending ? (
          <output className="block py-10 text-center text-sm text-muted-foreground">
            Cargando recogidas…
          </output>
        ) : null}
        {entregas.isError ? (
          <div
            role="alert"
            className="flex flex-wrap items-center gap-3 rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
          >
            <span>No pudimos cargar las recogidas.</span>
            <Button
              variant="outline"
              size="sm"
              className="min-h-9"
              onClick={() => entregas.refetch()}
            >
              Reintentar
            </Button>
          </div>
        ) : null}
        {entregas.isSuccess ? (
          <AdminDataTable
            caption="Recogidas de la tienda por confirmar"
            columns={[
              { key: "pedido", label: "Pedido", identificador: true },
              { key: "comprador", label: "Comprador" },
              { key: "productos", label: "Productos" },
              { key: "total", label: "Total", numerico: true },
              { key: "fecha", label: "Creado", numerico: true },
              { key: "acciones", label: "Acciones" },
            ]}
            filas={entregas.data.pendientes.map((entrega) => ({
              cells: {
                pedido: entrega.pedido_id,
                comprador: (
                  <div>
                    <p className="font-medium text-foreground">
                      {entrega.comprador_nombres} {entrega.comprador_apellidos}
                    </p>
                    <p className="text-caption text-muted-foreground">
                      DNI: {entrega.comprador_documento}
                    </p>
                  </div>
                ),
                productos: entrega.lineas
                  .map(
                    (linea) => `${linea.cantidad} × ${linea.concepto_nombre}`,
                  )
                  .join(", "),
                total:
                  entrega.moneda === "PEN"
                    ? formatoMoneda.format(entrega.total)
                    : `${entrega.moneda} ${entrega.total.toFixed(2)}`,
                fecha: formatoFecha.format(new Date(entrega.created_at)),
                acciones: (
                  <Button
                    type="button"
                    size="sm"
                    className="min-h-9"
                    onClick={() => setPedidoPorConfirmar(entrega.pedido_id)}
                  >
                    Confirmar entrega
                  </Button>
                ),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={PackageCheck}
                title="No hay recogidas pendientes"
                description="Todos los pedidos pagados ya fueron entregados o todavía no hay compras listas para retirar."
              />
            }
          />
        ) : null}
      </AdminPanel>

      <AdminPanel
        title="Recogidas entregadas"
        description="Actas ya registradas por el personal de la tienda."
      >
        {entregas.isSuccess ? (
          <AdminDataTable
            caption="Recogidas entregadas de la tienda"
            columns={[
              { key: "pedido", label: "Pedido", identificador: true },
              { key: "comprador", label: "Comprador" },
              { key: "productos", label: "Productos" },
              { key: "total", label: "Total", numerico: true },
              { key: "fecha", label: "Entregado", numerico: true },
            ]}
            filas={entregas.data.entregadas.map((entrega) => ({
              cells: {
                pedido: entrega.pedido_id,
                comprador: (
                  <div>
                    <p className="font-medium text-foreground">
                      {entrega.comprador_nombres} {entrega.comprador_apellidos}
                    </p>
                    <p className="text-caption text-muted-foreground">
                      DNI: {entrega.comprador_documento}
                    </p>
                  </div>
                ),
                productos: entrega.lineas
                  .map(
                    (linea) => `${linea.cantidad} × ${linea.concepto_nombre}`,
                  )
                  .join(", "),
                total:
                  entrega.moneda === "PEN"
                    ? formatoMoneda.format(entrega.total)
                    : `${entrega.moneda} ${entrega.total.toFixed(2)}`,
                fecha: formatoFecha.format(new Date(entrega.entregada_en)),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={PackageCheck}
                title="Todavía no hay recogidas entregadas"
                description="Las entregas confirmadas aparecerán aquí con los datos del comprador."
              />
            }
          />
        ) : null}
      </AdminPanel>

      <AlertDialog
        open={pedidoPorConfirmar !== null}
        onOpenChange={(open) => !open && setPedidoPorConfirmar(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar entrega</AlertDialogTitle>
            <AlertDialogDescription>
              Confirma solo cuando el pedido haya sido entregado. El servidor
              registra el acta y un reintento no duplica la entrega.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={confirmarEntrega.isPending}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmar}
              disabled={confirmarEntrega.isPending}
            >
              {confirmarEntrega.isPending ? (
                <LoaderCircle
                  className="size-4 animate-spin"
                  aria-hidden="true"
                />
              ) : null}
              Confirmar entrega
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
