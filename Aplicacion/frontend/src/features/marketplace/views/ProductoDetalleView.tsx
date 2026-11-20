"use client";

import { ArrowLeft, Package } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { RUTAS } from "@/lib/routes";
import { DialogoCheckoutTienda } from "../components/DialogoCheckoutTienda";
import { GaleriaProducto } from "../components/GaleriaProducto";
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
  const [cantidad, setCantidad] = useState(1);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SHOP-02"
        title="Producto del catálogo"
        description="La ficha del producto con su galería, su precio vigente y sus existencias, y el pedido a partir de ella."
        facts={[{ label: "Referencia", value: slug }]}
        actions={
          <Button asChild variant="outline" className="min-h-11">
            <Link href={RUTAS.publico.tienda}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a la tienda
            </Link>
          </Button>
        }
      />

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
          accion={reintentar ? { label: "Reintentar", onClick: reintentar } : undefined}
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
        <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
          <GaleriaProducto imagenes={producto.imagenes} />

          <section
            aria-labelledby="detalle-producto-titulo"
            className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <div className="flex flex-col gap-1">
              <h2
                id="detalle-producto-titulo"
                className="text-title-section text-foreground"
              >
                {producto.nombre}
              </h2>
              {producto.categoria_nombre ? (
                <p className="text-caption text-muted-foreground">
                  {producto.categoria_nombre}
                </p>
              ) : null}
            </div>

            {producto.descripcion ? (
              <p className="text-sm text-muted-foreground">
                {producto.descripcion}
              </p>
            ) : null}

            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatearMonto(producto.precio_efectivo, moneda ?? "")}
              {producto.oferta_activa && producto.precio_oferta !== null ? (
                <span className="ml-2 text-sm font-normal text-muted-foreground line-through">
                  {formatearMonto(producto.precio, moneda ?? "")}
                </span>
              ) : null}
            </p>

            <div className="flex flex-col gap-2">
              <label
                htmlFor="cantidad-producto"
                className="text-sm font-medium text-foreground"
              >
                Cantidad
              </label>
              <Input
                id="cantidad-producto"
                type="number"
                inputMode="numeric"
                min={1}
                value={cantidad}
                onChange={(evento) => {
                  const siguiente = Number.parseInt(evento.target.value, 10);
                  if (Number.isNaN(siguiente) || siguiente < 1) return;
                  setCantidad(siguiente);
                }}
                aria-describedby="cantidad-producto-descripcion"
                className="min-h-11 w-24 text-center tabular-nums"
              />
              <p
                id="cantidad-producto-descripcion"
                className="text-caption text-muted-foreground"
              >
                La cantidad máxima y el stock los confirma el servidor al
                crear el pedido.
              </p>
            </div>

            {motivoBloqueo ? (
              <p className="text-caption font-semibold text-destructive">
                {motivoBloqueo}
              </p>
            ) : null}

            <Button
              type="button"
              className="min-h-11 w-full"
              disabled={Boolean(motivoBloqueo)}
              onClick={() => setDialogoAbierto(true)}
            >
              Comprar
            </Button>
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
        />
      ) : null}
    </div>
  );
}
