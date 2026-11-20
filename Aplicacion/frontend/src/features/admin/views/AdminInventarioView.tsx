"use client";

import { Boxes, ClipboardList, Hash, Plus, Type } from "lucide-react";
import { useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import {
  useInventarioMarketplace,
  useRegistrarMovimientoInventario,
} from "@/features/marketplace/hooks/useInventarioMarketplace";
import {
  type InventarioProducto,
  type MovimientoInventarioFormData,
  movimientoInventarioFormSchema,
} from "@/features/marketplace/schemas/inventario.schema";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-19 - the stock movements of the store.
 *
 * Stock is not a number that is edited: it is the sum of the movements.
 * The route shows the movements, and the movements are the record.
 */
export function AdminInventarioView() {
  const [modalAbierto, setModalAbierto] = useState(false);
  const inventario = useInventarioMarketplace();
  const registrar = useRegistrarMovimientoInventario();
  const productos = inventario.data ?? [];

  const movimientoNuevo = (
    <Button
      type="button"
      className="min-h-11"
      onClick={() => setModalAbierto(true)}
      disabled={productos.length === 0}
    >
      <Plus className="size-4" aria-hidden="true" />
      Registrar movimiento
    </Button>
  );

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-19"
        title="Registrar movimientos de stock"
        description="Las entradas y las salidas de existencias de la tienda, con su motivo y su fecha."
        actions={movimientoNuevo}
      />

      <AdminSubnav
        ariaLabel="Secciones de la tienda"
        items={[
          {
            href: RUTAS.administracion.marketplace,
            label: "Tienda",
            description: "Productos y pedidos",
          },
          {
            href: RUTAS.administracion.marketplaceInventario,
            label: "Inventario",
            description: "Movimientos de stock",
          },
        ]}
      />

      <AdminNotice title="Las existencias son la suma de los movimientos">
        Esta pantalla no edita una cifra de stock: registra los movimientos que
        la componen. El saldo que se vea en el producto es el que calcula el
        backend.
      </AdminNotice>

      <AdminPanel
        title="Movimientos"
        description="Las entradas y salidas de existencias, con su cantidad y su motivo."
        actions={movimientoNuevo}
      >
        {inventario.isPending ? (
          <p
            role="status"
            className="py-10 text-center text-sm text-muted-foreground"
          >
            Cargando inventario...
          </p>
        ) : null}
        {inventario.isError ? (
          <p
            role="alert"
            className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
          >
            No pudimos cargar el inventario.
          </p>
        ) : null}
        {inventario.isSuccess ? (
          <AdminDataTable
            caption="Movimientos de stock de la tienda"
            columns={[
              { key: "producto", label: "Producto" },
              { key: "stock", label: "Stock", numerico: true },
              { key: "reservado", label: "Reservado", numerico: true },
              { key: "disponible", label: "Disponible", numerico: true },
              { key: "referencia", label: "Referencia", identificador: true },
              { key: "cantidad", label: "Cantidad", numerico: true },
              { key: "tipo", label: "Tipo" },
              { key: "fecha", label: "Fecha", numerico: true },
            ]}
            filas={productos.flatMap((producto) =>
              producto.movimientos.map((movimiento) => ({
                cells: {
                  producto: producto.nombre,
                  stock: producto.stock,
                  reservado: producto.reservado,
                  disponible: producto.disponible,
                  referencia: movimiento.referencia,
                  cantidad:
                    movimiento.cantidad > 0
                      ? `+${movimiento.cantidad}`
                      : movimiento.cantidad,
                  tipo: movimiento.tipo,
                  fecha: new Date(movimiento.created_at).toLocaleString(
                    "es-PE",
                  ),
                },
              })),
            )}
            vacio={
              <AdminEmptyState
                icon={Boxes}
                title={
                  productos.length === 0
                    ? "Todavía no hay productos para inventariar"
                    : "Todavía no hay movimientos de stock"
                }
                description={
                  productos.length === 0
                    ? "Crea un producto en Tienda antes de registrar sus existencias."
                    : "Registra la primera reposición, salida o ajuste de inventario."
                }
                action={productos.length > 0 ? movimientoNuevo : undefined}
              />
            }
          />
        ) : null}
      </AdminPanel>

      {modalAbierto ? (
        <AppFormModal<MovimientoInventarioFormData>
          open={modalAbierto}
          onOpenChange={setModalAbierto}
          title="Registrar movimiento"
          description="El saldo lo calcula el servidor a partir de esta bitácora inmutable."
          primaryLabel="Registrar"
          primaryLoadingLabel="Registrando..."
          primaryLoading={registrar.isPending}
          onPrimary={() => undefined}
          schema={movimientoInventarioFormSchema}
          initialData={{
            producto_id: "",
            tipo: "REPOSICION",
            cantidad: 1,
            motivo: "",
          }}
          onSubmit={async (datos) => {
            await registrar.mutateAsync(datos);
            await inventario.refetch();
          }}
        >
          {({ methods }) => (
            <CamposMovimiento methods={methods} productos={productos} />
          )}
        </AppFormModal>
      ) : null}
    </div>
  );
}

/**
 * Los campos del movimiento de stock.
 *
 * El formulario es el Modo 1 (`children`): `FormField` dibuja la etiqueta, el
 * icono y el error de cada campo. Los dos selectores son campos CONTROLADOS:
 * su valor se lee con `useController` ACOTADO a su campo, nunca con un
 * `watch()` global.
 */
function CamposMovimiento({
  methods,
  productos,
}: {
  methods: UseFormReturn<MovimientoInventarioFormData>;
  productos: InventarioProducto[];
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: producto } = useController({
    control: controlFormulario,
    name: "producto_id",
  });
  const { field: tipo } = useController({
    control: controlFormulario,
    name: "tipo",
  });

  return (
    <FormGrid>
      <FormField
        id="movimiento-producto"
        label="Producto"
        required
        icon={Boxes}
        span={12}
        error={errors.producto_id?.message}
      >
        {(control) => (
          <Select
            value={producto.value}
            onValueChange={producto.onChange}
            disabled={productos.length === 0}
          >
            <SelectTrigger
              {...control}
              onBlur={producto.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige el producto" />
            </SelectTrigger>
            <SelectContent>
              {productos.map((productoActual) => (
                <SelectItem
                  key={productoActual.producto_id}
                  value={productoActual.producto_id}
                >
                  {productoActual.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="movimiento-tipo"
        label="Tipo"
        required
        icon={ClipboardList}
        span={6}
        helper="Una reposición suma existencias y una salida las resta."
        error={errors.tipo?.message}
      >
        {(control) => (
          <Select value={tipo.value} onValueChange={tipo.onChange}>
            <SelectTrigger {...control} onBlur={tipo.onBlur} className="w-full">
              <SelectValue placeholder="Elige el tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="REPOSICION">Reposición</SelectItem>
              <SelectItem value="MERMA">Merma</SelectItem>
              <SelectItem value="CONSUMO_INTERNO">Consumo interno</SelectItem>
              <SelectItem value="SALIDA_SIN_VENTA">Salida sin venta</SelectItem>
              <SelectItem value="AJUSTE">Ajuste</SelectItem>
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="movimiento-cantidad"
        label="Cantidad con signo"
        required
        icon={Hash}
        span={6}
        helper="Positiva para una reposición, negativa para una salida."
        error={errors.cantidad?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("cantidad", { valueAsNumber: true })}
            type="number"
            step="1"
            inputMode="numeric"
          />
        )}
      </FormField>

      <FormField
        id="movimiento-motivo"
        label="Motivo"
        required
        icon={Type}
        span={12}
        helper="Queda escrito en el acta del movimiento."
        error={errors.motivo?.message}
      >
        {(control) => (
          <Textarea
            {...control}
            {...register("motivo")}
            rows={3}
            maxLength={200}
          />
        )}
      </FormField>
    </FormGrid>
  );
}
