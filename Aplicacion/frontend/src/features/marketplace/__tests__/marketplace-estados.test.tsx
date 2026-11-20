// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { pedidoSeguimientoSchema } from "../schemas/pedido.schema";
import {
  categoriaListaSchema,
  productoDetalleSchema,
  productoListItemSchema,
} from "../schemas/producto.schema";
import type {
  EstadoDeclarado,
  VeredictoPago,
} from "../types/marketplace.types";
import { PedidoSeguimientoView } from "../views/PedidoSeguimientoView";
import { ProductoDetalleView } from "../views/ProductoDetalleView";
import { TiendaCatalogoView } from "../views/TiendaCatalogoView";

/**
 * The states of the store routes.
 *
 * **There is NO provisional fixture anymore.** The data is the answer of the
 * CONTRACT, parsed by the same Zod mirrors the service uses: a shape that
 * the mirror rejects breaks the suite before it renders anything.
 */
const CATEGORIA = categoriaListaSchema.parse({
  id: "00000000-0000-4000-8000-0000000000a1",
  nombre: "CATEGORIA DE EJEMPLO",
  slug: "categoria-de-ejemplo",
  orden: 1,
});

const PRODUCTO = productoListItemSchema.parse({
  id: "00000000-0000-4000-8000-0000000000a2",
  nombre: "PRODUCTO DE EJEMPLO",
  slug: "producto-de-ejemplo",
  categoria_id: CATEGORIA.id,
  categoria_nombre: CATEGORIA.nombre,
  precio: 0,
  precio_oferta: 0,
  precio_efectivo: 0,
  oferta_activa: true,
  estado: "ACTIVO",
  imagen_principal_url: null,
  cantidad_imagenes: 1,
});
const DETALLE = productoDetalleSchema.parse({
  ...PRODUCTO,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  edicion_id: "00000000-0000-4000-8000-000000000001",
  edicion_nombre: "EDICION DE EJEMPLO",
  descripcion: " merchandising del festival.",
  oferta_inicia: null,
  oferta_termina: null,
  imagenes: [
    {
      id: "00000000-0000-4000-8000-0000000000a3",
      orden: 1,
      url: null,
      es_principal: true,
      texto_alternativo: "CAMISETA DEL FESTIVAL",
      disponible: false,
      created_at: "2026-01-01T00:00:00Z",
    },
  ],
});

const PEDIDO = pedidoSeguimientoSchema.parse({
  id: "00000000-0000-4000-8000-0000000000a4",
  estado: "PAGADO",
  estado_pago: "PAGADA",
  estado_entrega: "PENDIENTE",
  total: 0,
  moneda: "PEN",
  lineas: [
    {
      tipo_concepto: "PRODUCTO",
      concepto_id: PRODUCTO.id,
      concepto_nombre: PRODUCTO.nombre,
      cantidad: 1,
      precio_unitario: 0,
      precio_aplicado: 0,
      subtotal: 0,
    },
  ],
  orden_pago_id: null,
  siguientes_acciones: [],
  created_at: "2026-01-01T00:00:00Z",
});

const ENTREGA: EstadoDeclarado = {
  codigo: "PENDIENTE",
  etiqueta: "Pendiente de entrega",
};
const PAGO_CONFIRMADO: VeredictoPago = {
  estado: {
    codigo: "PAGADA",
    etiqueta: "Pagada",
    descripcion: "El pago está confirmado y la compra consta como pagada.",
  },
  rol: "confirmado",
};

const PAGO_PENDIENTE: VeredictoPago = {
  estado: {
    codigo: "PENDIENTE",
    etiqueta: "Pendiente",
    descripcion: "El pago todavía no se ha completado.",
  },
  rol: "pendiente",
};

describe("SHOP-01 - el catálogo de la tienda", () => {
  it("sin datos dice que el catálogo no está disponible", () => {
    render(<TiendaCatalogoView />);

    expect(
      screen.getByText("El catálogo de la tienda todavía no está disponible"),
    ).toBeDefined();
  });

  it("el error ofrece reintentar", () => {
    render(<TiendaCatalogoView estado="error" reintentar={() => {}} />);

    expect(
      screen.getByText("No pudimos cargar el catálogo de la tienda"),
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();
  });

  it("un catálogo vacío lo dice y no inventa productos", () => {
    render(<TiendaCatalogoView estado="listo" productos={[]} />);

    expect(
      screen.getByText("No hay productos publicados en esta edición"),
    ).toBeDefined();
  });

  it("una categoría sin productos ofrece quitar el filtro", () => {
    render(
      <TiendaCatalogoView
        estado="listo"
        productos={[]}
        categorias={[CATEGORIA]}
        categoriaActiva={CATEGORIA.slug}
      />,
    );

    expect(
      screen.getByText("No hay productos en esta categoría"),
    ).toBeDefined();
    expect(
      screen.getByRole("link", { name: "Quitar el filtro" }),
    ).toBeDefined();
  });

  it("con datos muestra el producto y su precio", () => {
    render(
      <TiendaCatalogoView estado="listo" productos={[PRODUCTO]} moneda="PEN" />,
    );

    expect(screen.getAllByText("PRODUCTO DE EJEMPLO")[0]).toBeDefined();
    expect(screen.getByText("Oferta")).toBeDefined();
  });
});
describe("SHOP-02 - la ficha del producto", () => {
  it("sin datos no muestra una ficha inventada", () => {
    render(<ProductoDetalleView slug="producto-de-ejemplo" />);

    expect(
      screen.getByText("Este producto todavía no se puede mostrar"),
    ).toBeDefined();
  });

  it("la galería anuncia su posición y es navegable con el teclado", () => {
    render(
      <ProductoDetalleView
        slug="producto-de-ejemplo"
        estado="listo"
        producto={DETALLE}
      />,
    );

    expect(screen.getByText("Imagen 1 de 1")).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Imagen anterior" }),
    ).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Imagen siguiente" }),
    ).toBeDefined();
  });

  it("la imagen que no está en el volumen conserva su texto alternativo", () => {
    render(
      <ProductoDetalleView
        slug="producto-de-ejemplo"
        estado="listo"
        producto={DETALLE}
      />,
    );

    expect(screen.getByText("CAMISETA DEL FESTIVAL")).toBeDefined();
  });

  it("el precio lo publica el servidor y el total no se calcula aquí", () => {
    render(
      <ProductoDetalleView
        slug="producto-de-ejemplo"
        estado="listo"
        producto={DETALLE}
        moneda="PEN"
      />,
    );

    expect(screen.getAllByText("PEN 0.00").length).toBeGreaterThan(0);
    expect(screen.queryByText(/total/i)).toBeNull();
  });
});
describe("SHOP-03 - el seguimiento del pedido", () => {
  it("sin datos no afirma ningún pago", () => {
    render(<PedidoSeguimientoView token="abc123" />);

    expect(
      screen.getByText("Este pedido todavía no se puede mostrar"),
    ).toBeDefined();
  });

  it("el rechazo es neutral: no dice si el pedido existe", () => {
    render(<PedidoSeguimientoView token="abc123" estado="sin-permiso" />);

    expect(screen.getByText("No pudimos abrir este pedido")).toBeDefined();
    expect(screen.queryByText(/pedido encontrado/i)).toBeNull();
  });

  it("un pedido pagado y no entregado nunca lee como entregado", () => {
    render(
      <PedidoSeguimientoView
        token="abc123"
        estado="listo"
        pedido={PEDIDO}
        pago={PAGO_CONFIRMADO}
        entrega={ENTREGA}
      />,
    );

    // El pago y la entrega son DOS líneas y dos hechos.
    expect(screen.getByText("Pago")).toBeDefined();
    expect(screen.getByText("Entrega")).toBeDefined();
    expect(screen.getByText("Pagada")).toBeDefined();
    expect(screen.getByText("Pendiente de entrega")).toBeDefined();
    expect(screen.queryByText("Entregado")).toBeNull();
  });

  it("el pago pendiente no se presenta como confirmado", () => {
    render(
      <PedidoSeguimientoView
        token="abc123"
        estado="listo"
        pedido={PEDIDO}
        pago={PAGO_PENDIENTE}
        entrega={ENTREGA}
      />,
    );

    expect(screen.getByText("Pendiente")).toBeDefined();
    expect(screen.queryByText("Pagada")).toBeNull();
  });
});
const FUENTES = [
  "components/EstadoPagoTienda.tsx",
  "components/TarjetaProducto.tsx",
  "components/GaleriaProducto.tsx",
  "views/TiendaCatalogoView.tsx",
  "views/ProductoDetalleView.tsx",
  "views/PedidoSeguimientoView.tsx",
];

describe("la zona de la tienda no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "marketplace", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("la zona de la tienda cumple el contrato de los cinco anchos", () => {
  it.each(FUENTES)("%s usa objetivos táctiles de 44 px", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "marketplace", ruta),
      "utf8",
    );

    expect(fuente).toContain("min-h-11");
  });
});
