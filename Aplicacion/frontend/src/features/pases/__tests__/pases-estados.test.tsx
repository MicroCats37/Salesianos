// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  catalogoPasesSchema,
  compraPasesSchema,
} from "../schemas/pase.schema";
import type { VeredictoPago } from "../types/pase.types";
import { adaptarCompra } from "../utils/pase.adaptador.utils";
import { PaseGestionarView } from "../views/PaseGestionarView";
import { PasesView } from "../views/PasesView";

/**
 * The states of the pass routes.
 *
 * The suite walks the states of `SH-03` on `PASS-01` and `PASS-02`: the
 * honest empty, the recoverable error, the populated catalogue, the neutral
 * denial and the presentable payment states.
 *
 * **There is NO provisional fixture anymore.** The data is the answer of the
 * CONTRACT, parsed by the same Zod mirror the service uses: a shape that the
 * mirror rejects breaks the suite before it renders anything.
 */
const CATALOGO = catalogoPasesSchema.parse({
  edicion_id: "00000000-0000-4000-8000-000000000001",
  edicion_nombre: "EDICION DE EJEMPLO",
  pases: [
    {
      id: "00000000-0000-4000-8000-0000000000c1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      edicion_id: "00000000-0000-4000-8000-000000000001",
      edicion_nombre: "EDICION DE EJEMPLO",
      nombre: "PASE DE EJEMPLO",
      slug: "pase-de-ejemplo",
      descripcion: "Entrada nominativa a la fiesta.",
      estado: "VIGENTE",
      precio: {
        monto: 0,
        moneda: "PEN",
        vigente_desde: "2026-01-01",
        vigente_hasta: null,
      },
    },
  ],
});

const COMPRA = adaptarCompra(
  compraPasesSchema.parse({
    compra_pase_id: "00000000-0000-4000-8000-0000000000e1",
    estado: "PAGADA",
    cantidad: 2,
    asignados: 1,
    disponibles: 1,
    beneficiarios: [
      {
        id: "00000000-0000-4000-8000-0000000000d1",
        pase_id: "00000000-0000-4000-8000-0000000000c1",
        pase_nombre: "PASE DE EJEMPLO",
        edicion_id: "00000000-0000-4000-8000-000000000001",
        persona_id: "00000000-0000-4000-8000-0000000000b2",
        persona_nombres: "PERSONA",
        persona_apellidos: "DE EJEMPLO",
        persona_tipo_documento: "DNI",
        persona_numero_documento: "00000000",
        origen: "COMPRA",
        estado: "ACTIVO",
        cantidad: 1,
        cantidad_consumida: 0,
        cantidad_disponible: 1,
        asignado_en: "2026-01-01T00:00:00Z",
        motivo: "",
        revocado_en: null,
        motivo_revocacion: "",
      },
    ],
    compra_id: "00000000-0000-4000-8000-0000000000b1",
    orden_pago_id: "00000000-0000-4000-8000-0000000000f1",
    pase_id: "00000000-0000-4000-8000-0000000000c1",
    pase_nombre: "PASE DE EJEMPLO",
    edicion_nombre: "EDICION DE EJEMPLO",
    precio_unitario: 0,
    total: 0,
    moneda: "PEN",
    causa_operativa: "COMPRA_PASE_CREADA",
  }),
);
describe("PASS-01 - el catálogo de pases", () => {
  it("sin datos dice que el catálogo no está disponible", () => {
    render(<PasesView />);

    expect(
      screen.getByText("El catálogo de pases todavía no está disponible"),
    ).toBeDefined();
  });

  it("el error ofrece reintentar", () => {
    render(<PasesView estado="error" reintentar={() => {}} />);

    expect(
      screen.getByText("No pudimos cargar el catálogo de pases"),
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();
  });

  it("con datos muestra el pase y el precio que publicó el servidor", () => {
    render(<PasesView estado="listo" catalogo={CATALOGO} />);

    expect(screen.getByText("PASE DE EJEMPLO")).toBeDefined();
    expect(screen.getByText("PEN 0.00")).toBeDefined();
  });

  it("un catálogo vacío lo dice y no inventa pases", () => {
    render(<PasesView estado="listo" catalogo={{ ...CATALOGO, pases: [] }} />);

    expect(
      screen.getByText("No hay pases a la venta en esta edición"),
    ).toBeDefined();
  });

  it("la descarga en curso no inventa un catálogo", () => {
    render(<PasesView estado="cargando" />);

    expect(screen.getByText("Cargando el catálogo de pases")).toBeDefined();
    expect(
      screen.queryByText("El catálogo de pases todavía no está disponible"),
    ).toBeNull();
  });
});

describe("PASS-02 - la gestión de los beneficiarios", () => {
  it("sin datos no afirma ninguna asignación", () => {
    render(<PaseGestionarView token="abc123" />);

    expect(
      screen.getByText("El enlace todavía no se puede comprobar"),
    ).toBeDefined();
  });

  it("el rechazo es neutral: no dice si la compra existe", () => {
    render(<PaseGestionarView token="abc123" estado="sin-permiso" />);

    expect(screen.getByText("No pudimos abrir esta compra")).toBeDefined();
    expect(screen.queryByText(/compra encontrada/i)).toBeNull();
    expect(screen.queryByText(/no existe/i)).toBeNull();
  });
});
describe("PASS-02 - la compra y sus titulares", () => {
  it("con datos muestra los tres contadores y la lista de personas", () => {
    render(
      <PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />,
    );

    expect(screen.getByText("Adquiridos")).toBeDefined();
    expect(screen.getByText("Asignados")).toBeDefined();
    expect(screen.getByText("Pendientes")).toBeDefined();
    expect(screen.getByText("PERSONA DE EJEMPLO")).toBeDefined();
  });

  it("el estado del lote y el de cada derecho son etiquetas, no códigos", () => {
    render(
      <PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />,
    );

    expect(screen.getByText("Compra pagada")).toBeDefined();
    expect(screen.getByText("Entrada activa")).toBeDefined();
    expect(screen.queryByText("PAGADA")).toBeNull();
    expect(screen.queryByText("ACTIVO")).toBeNull();
  });

  it("el formulario de asignación está disponible mientras hay cupo", () => {
    render(
      <PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />,
    );

    expect(screen.getByText("Asignar una entrada")).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Asignar el pase" }),
    ).toBeDefined();
  });
});
describe("los estados presentables del pago", () => {
  const ESTADOS: [VeredictoPago, string][] = [
    [
      {
        estado: {
          codigo: "PENDIENTE",
          etiqueta: "Pendiente",
          descripcion: "El pago todavía no se ha completado.",
        },
        rol: "pendiente",
      },
      "Pendiente",
    ],
    [
      {
        estado: {
          codigo: "PAGADA",
          etiqueta: "Pagada",
          descripcion: "El pago está confirmado y la compra consta como pagada.",
        },
        rol: "confirmado",
      },
      "Pagada",
    ],
    [
      {
        estado: {
          codigo: "PAGADA_SIN_LIQUIDAR",
          etiqueta: "Pagada sin liquidar",
          descripcion:
            "El pago está confirmado y la compra todavía no figura como pagada.",
        },
        rol: "atencion",
      },
      "Pagada sin liquidar",
    ],
    [
      {
        estado: {
          codigo: "CANCELADA",
          etiqueta: "Cancelada",
          descripcion: "La orden de pago o la compra fueron canceladas.",
        },
        rol: "sin-confirmar",
      },
      "Cancelada",
    ],
    [
      {
        estado: {
          codigo: "VENCIDA",
          etiqueta: "Vencida",
          descripcion: "La orden de pago venció sin completarse.",
        },
        rol: "sin-confirmar",
      },
      "Vencida",
    ],
  ];

  for (const [veredicto, etiqueta] of ESTADOS) {
    it(`el estado "${etiqueta}" se presenta con la etiqueta del backend`, () => {
      render(
        <PaseGestionarView
          token="abc123"
          estado="listo"
          compra={COMPRA}
          pago={veredicto}
        />,
      );

      expect(screen.getByText(etiqueta)).toBeDefined();
      expect(screen.queryByText(veredicto.estado.codigo)).toBeNull();
    });
  }
});
const FUENTES = [
  "components/EstadoPagoPase.tsx",
  "components/TarjetaPase.tsx",
  "components/ResumenCompra.tsx",
  "components/FormularioComprador.tsx",
  "components/FormularioBeneficiario.tsx",
  "views/PasesView.tsx",
  "views/PaseGestionarView.tsx",
];

describe("la zona de pases no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "pases", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("la zona de pases cumple el contrato de los cinco anchos", () => {
  it.each(FUENTES)("%s usa objetivos táctiles de 44 px", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "pases", ruta),
      "utf8",
    );

    expect(fuente).toContain("min-h-11");
  });
});