"use client";

import { ArrowLeft, Minus, Package, Plus, ShoppingBag } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { FestivalPublicPage } from "@/components/shell/FestivalPublicPage";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RUTAS } from "@/lib/routes";
import { DialogoCheckoutTienda } from "../components/DialogoCheckoutTienda";
import { GaleriaProducto } from "../components/GaleriaProducto";
import type { CrearPedido } from "../schemas/pedido.schema";
import { crearPedido } from "../services/marketplace.service";
import type {
  EstadoVistaTienda,
  ProductoDetalle,
  VeredictoPago,
} from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";

export interface ProductoDetalleViewProps {
  /** The slug of the product, the identity in the URL. */
  slug: string;
  /** The state of the product. */
  estado?: EstadoVistaTienda;
  /** The product, when it is published. */
  producto?: ProductoDetalle;
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /** The currency of the price, when the edition publishes one. */
  moneda?: string;
  /** The reason why the product cannot be bought. */
  motivoBloqueo?: string;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the
   * server chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}

/**
 * SHOP-02 - the detail of a product and the creation of its order.
 *
 * The slug is the identity of the product in the URL. The page shows what
 * the server publishes about it: its price, its availability and its
 * gallery. It never invents a price to be able to offer a "buy" button.
 *
 * The price and the availability shown after the re-validation are the
 * BACKEND's: the browser never recomputes them (`RB-02` SHOP-02).
 */
export function ProductoDetalleView({
  slug,
  estado = "sin-datos",
  producto,
  pago,
  moneda,
  motivoBloqueo,
  mensajeError,
  reintentar,
}: ProductoDetalleViewProps) {
  const router = useRouter();
  const [cantidad, setCantidad] = useState(1);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);

  async function crearPedidoYContinuar(comprador: Omit<CrearPedido, "items">) {
    if (!producto) return;
    const pedido = await crearPedido({
      ...comprador,
      items: [{ tipo: "PRODUCTO", producto_id: producto.id, cantidad }],
    });
    setDialogoAbierto(false);
    router.push(`/tienda/pedidos/${encodeURIComponent(pedido.token)}`);
  }

  return (
    <FestivalPublicPage
      eyebrow="TIENDA / SALESIANOS FEST"
      title={
        producto
          ? ["LLEVA EL", "FESTIVAL", "CONTIGO."]
          : ["TU COMPRA", "DEL FESTIVAL."]
      }
      highlighted={producto ? "CONTIGO." : "FESTIVAL."}
      description="Elige tu producto, confirma la cantidad y continúa como invitado. El servidor valida el precio, el stock y el pago."
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          asChild
          variant="outline"
          className="min-h-11 bg-surface-raised"
        >
          <Link href={RUTAS.publico.tienda}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            Volver a la tienda
          </Link>
        </Button>
        <p className="text-caption text-muted-foreground">Referencia: {slug}</p>
      </div>

      {estado === "sin-permiso" ? (
        <ShellPermissionDenied
          title="No podemos mostrarte este producto"
          description="Esta zona del festival no está disponible para ti ahora mismo."
          className="border-border bg-surface-raised"
        />
      ) : null}

      {estado === "cargando" ? (
        <ShellPendingState
          title="Cargando el producto"
          description="Estamos leyendo la ficha y la galería del producto."
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar este producto"
          description={
            mensajeError ??
            "No pudimos leer la ficha del producto en este momento. Vuelve a intentarlo en unos segundos."
          }
          accion={
            reintentar
              ? { label: "Reintentar", onClick: reintentar }
              : undefined
          }
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={Package}
          title="Este producto todavía no se puede mostrar"
          description="La ficha del producto la publica el servicio de la tienda con su precio y su stock. Cuando el servicio este conectado, aquí se verán sus imagenes y el pedido se podrá crear desde esta misma pantalla."
        />
      ) : null}

      {estado === "listo" && producto ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(20rem,5fr)] lg:items-start">
          <GaleriaProducto
            imagenes={producto.imagenes}
            className="rounded-[var(--radius-xl)] border border-border bg-surface-raised p-3 shadow-sm"
          />

          <section
            aria-labelledby="detalle-producto-titulo"
            className="flex flex-col gap-6 rounded-[var(--radius-xl)] border border-border bg-surface-raised p-5 shadow-sm sm:p-6"
          >
            <div className="flex flex-col gap-3">
              {producto.categoria_nombre ? (
                <p className="text-caption font-semibold text-eyebrow-brand">
                  {producto.categoria_nombre}
                </p>
              ) : null}
              <h2
                id="detalle-producto-titulo"
                className="text-title-section text-foreground"
              >
                {producto.nombre}
              </h2>
              <p className="text-2xl font-semibold tabular-nums text-foreground sm:text-3xl">
                {formatearMonto(producto.precio_efectivo, moneda ?? "")}
                {producto.oferta_activa && producto.precio_oferta !== null ? (
                  <span className="ml-3 text-sm font-normal text-muted-foreground line-through">
                    {formatearMonto(producto.precio, moneda ?? "")}
                  </span>
                ) : null}
              </p>
            </div>

            {producto.descripcion ? (
              <p className="text-sm text-muted-foreground">
                {producto.descripcion}
              </p>
            ) : null}

            <div className="rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    Cantidad
                  </p>
                  <p
                    id="cantidad-producto-descripcion"
                    className="text-caption text-muted-foreground"
                  >
                    El stock final se confirma al crear el pedido.
                  </p>
                </div>
                <div className="flex items-center rounded-[var(--radius-md)] border border-border bg-surface-raised">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="min-h-11 min-w-11"
                    disabled={cantidad === 1}
                    onClick={() =>
                      setCantidad((actual) => Math.max(1, actual - 1))
                    }
                    aria-label="Reducir cantidad"
                  >
                    <Minus className="size-4" aria-hidden="true" />
                  </Button>
                  <Input
                    id="cantidad-producto"
                    type="number"
                    inputMode="numeric"
                    min={1}
                    value={cantidad}
                    onChange={(evento) => {
                      const siguiente = Number.parseInt(
                        evento.target.value,
                        10,
                      );
                      if (Number.isNaN(siguiente) || siguiente < 1) return;
                      setCantidad(siguiente);
                    }}
                    aria-describedby="cantidad-producto-descripcion"
                    className="h-11 w-12 border-y-0 border-x text-center tabular-nums focus-visible:ring-0"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="min-h-11 min-w-11"
                    onClick={() => setCantidad((actual) => actual + 1)}
                    aria-label="Aumentar cantidad"
                  >
                    <Plus className="size-4" aria-hidden="true" />
                  </Button>
                </div>
              </div>
            </div>

            {motivoBloqueo ? (
              <p className="text-caption font-semibold text-destructive">
                {motivoBloqueo}
              </p>
            ) : null}

            <Button
              type="button"
              className="min-h-12 w-full text-base"
              disabled={Boolean(motivoBloqueo)}
              onClick={() => setDialogoAbierto(true)}
            >
              <ShoppingBag className="size-4" aria-hidden="true" />
              Comprar como invitado
            </Button>
            <p className="text-center text-caption text-muted-foreground">
              Ingresa tus datos y continúa al pago sin crear una cuenta.
            </p>
          </section>
        </div>
      ) : null}

      {estado === "listo" && producto ? (
        <DialogoCheckoutTienda
          producto={producto}
          cantidad={cantidad}
          abierto={dialogoAbierto}
          onOpenChange={setDialogoAbierto}
          pago={pago}
          moneda={moneda}
          crearPedido={crearPedidoYContinuar}
        />
      ) : null}
    </FestivalPublicPage>
  );
}
