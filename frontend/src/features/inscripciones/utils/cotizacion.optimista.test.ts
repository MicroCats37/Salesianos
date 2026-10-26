import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./cotizacion.optimista.ts";
const { precioOptimista } = (await import(specifier)) as {
  precioOptimista: (params: {
    cotizacion: {
      paquete_id: string;
      cantidad_cotizada: number;
      precio_unitario: number;
      total: number;
      estado: "ACTIVA" | "EXPIRADA";
    } | null;
    paqueteId: string;
    cantidad: number;
    precioPreventa: number | null;
    precioRegular: number | null;
  }) => {
    precioUnitario: number;
    total: number;
    totalRegular: number | null;
    confirmada: boolean;
    desfasada: boolean;
  };
};

const COTIZACION = {
  paquete_id: "pack-duo",
  cantidad_cotizada: 15,
  precio_unitario: 60,
  total: 900,
  estado: "ACTIVA" as const,
};

test("sin cotizacion usa el precio de preventa del catalogo", () => {
  const r = precioOptimista({
    cotizacion: null,
    paqueteId: "pack-duo",
    cantidad: 15,
    precioPreventa: 60,
    precioRegular: 70,
  });
  assert.equal(r.precioUnitario, 60);
  assert.equal(r.total, 900);
  assert.equal(r.totalRegular, 1050);
  assert.equal(r.confirmada, false);
  assert.equal(r.desfasada, false);
});

test("sin cotizacion y sin precio de preventa cae al precio regular", () => {
  const r = precioOptimista({
    cotizacion: null,
    paqueteId: "pack-duo",
    cantidad: 5,
    precioPreventa: null,
    precioRegular: 70,
  });
  assert.equal(r.precioUnitario, 70);
  assert.equal(r.total, 350);
});

test("la cotizacion que confirma paquete y cantidad manda", () => {
  const r = precioOptimista({
    cotizacion: COTIZACION,
    paqueteId: "pack-duo",
    cantidad: 15,
    precioPreventa: 60,
    precioRegular: 70,
  });
  assert.equal(r.total, 900);
  assert.equal(r.confirmada, true);
  assert.equal(r.desfasada, false);
});

test("cambiar la cantidad proyecta el total sin esperar al servidor", () => {
  const r = precioOptimista({
    cotizacion: COTIZACION,
    paqueteId: "pack-duo",
    cantidad: 16,
    precioPreventa: 60,
    precioRegular: 70,
  });
  assert.equal(r.precioUnitario, 60);
  assert.equal(r.total, 960);
  assert.equal(r.totalRegular, 1120);
  assert.equal(r.confirmada, false);
  assert.equal(r.desfasada, true);
});

test("sin descuento no hay precio regular que tachar", () => {
  const r = precioOptimista({
    cotizacion: null,
    paqueteId: "pack-duo",
    cantidad: 15,
    precioPreventa: 70,
    precioRegular: 70,
  });
  assert.equal(r.totalRegular, null);
});

test("una cotizacion de otro paquete no contamina la card", () => {
  const r = precioOptimista({
    cotizacion: COTIZACION,
    paqueteId: "pack-trio",
    cantidad: 20,
    precioPreventa: 60,
    precioRegular: 70,
  });
  assert.equal(r.precioUnitario, 60);
  assert.equal(r.total, 1200);
  assert.equal(r.confirmada, false);
  assert.equal(r.desfasada, true);
});

test("el precio unitario confirmado por el servidor prevalece sobre el catalogo", () => {
  const r = precioOptimista({
    cotizacion: { ...COTIZACION, precio_unitario: 55, total: 825 },
    paqueteId: "pack-duo",
    cantidad: 15,
    precioPreventa: 60,
    precioRegular: 70,
  });
  assert.equal(r.precioUnitario, 55);
  assert.equal(r.total, 825);
  assert.equal(r.confirmada, true);
});
