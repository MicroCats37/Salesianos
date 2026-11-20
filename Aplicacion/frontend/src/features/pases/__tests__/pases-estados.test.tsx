// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CatalogoPases } from "../components/CatalogoPases";
import { TarjetaPase } from "../components/TarjetaPase";
import { catalogoPasesSchema, compraPasesSchema } from "../schemas/pase.schema";
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
    render(<PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />);

    expect(screen.getByText("Adquiridos")).toBeDefined();
    expect(screen.getByText("Asignados")).toBeDefined();
    expect(screen.getByText("Pendientes")).toBeDefined();
    expect(screen.getByText("PERSONA DE EJEMPLO")).toBeDefined();
  });

  it("el estado del lote y el de cada derecho son etiquetas, no códigos", () => {
    render(<PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />);

    expect(screen.getByText("Compra pagada")).toBeDefined();
    expect(screen.getByText("Entrada activa")).toBeDefined();
    expect(screen.queryByText("PAGADA")).toBeNull();
    expect(screen.queryByText("ACTIVO")).toBeNull();
  });

  it("el formulario de asignación está disponible mientras hay cupo", () => {
    render(<PaseGestionarView token="abc123" estado="listo" compra={COMPRA} />);

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
          descripcion:
            "El pago está confirmado y la compra consta como pagada.",
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
/**
 * The files of the two zones that this change touched.
 *
 * The scan is a SOURCE scan on purpose: a colour literal is not a runtime
 * behaviour that a render could catch, and the rule of `SH-01` T-01 is that
 * NO touched file carries a literal colour.
 */
const FUENTES = [
  "pases/components/CatalogoPases.tsx",
  "pases/components/ContadoresPases.tsx",
  "pases/components/DialogoCheckout.tsx",
  "pases/components/DialogoRevocar.tsx",
  "pases/components/EstadoPagoPase.tsx",
  "pases/components/FormularioBeneficiario.tsx",
  "pases/components/FormularioComprador.tsx",
  "pases/components/ListaBeneficiarios.tsx",
  "pases/components/ResumenCompra.tsx",
  "pases/components/SelectorCantidad.tsx",
  "pases/components/TarjetaPase.tsx",
  "pases/views/PasesView.tsx",
  "pases/views/PaseGestionarView.tsx",
  "pagos/components/ChipPago.tsx",
  "pagos/components/EstadoPagoActivacion.tsx",
  "pagos/components/buckets.pago.ts",
];

/**
 * The files that declare an interactive target of their own.
 *
 * `EstadoPagoPase` is NOT in this list: it does not draw a button, it
 * delegates the call to action to the shared chip of the payment area. The
 * chip declares the 44 px target, and the suite proves that the delegation
 * really happens.
 */
const FUENTES_TACTILES = [
  "pases/components/CatalogoPases.tsx",
  "pases/components/DialogoCheckout.tsx",
  "pases/components/DialogoRevocar.tsx",
  "pases/components/ListaBeneficiarios.tsx",
  "pases/components/SelectorCantidad.tsx",
  "pases/components/TarjetaPase.tsx",
  "pases/views/PasesView.tsx",
  "pases/views/PaseGestionarView.tsx",
  "pagos/components/ChipPago.tsx",
];

/** The source of a file of `src/features`. */
function leer(ruta: string): string {
  return readFileSync(join(process.cwd(), "src", "features", ruta), "utf8");
}

/**
 * The forms whose touch target comes from the shared field.
 *
 * They are NOT in `FUENTES_TACTILES`: they do not declare `min-h-11` on
 * their own controls, they inherit it from `FormField`.
 */
const FUENTES_DELEGADOS = [
  "pases/components/FormularioBeneficiario.tsx",
  "pases/components/FormularioComprador.tsx",
];

describe("la zona de pases y de pagos no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = leer(ruta);

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("la zona de pases cumple el contrato de los cinco anchos", () => {
  it.each(FUENTES_TACTILES)("%s usa objetivos táctiles de 44 px", (ruta) => {
    expect(leer(ruta)).toContain("min-h-11");
  });

  /**
   * The forms that delegate their target to the SHARED field.
   *
   * `FormField` (`src/components/forms`) draws the label, the icon, the
   * error AND the 44 px target of the control, so a form that uses it does
   * not repeat `min-h-11` on its inputs: the guarantee is inherited, not
   * lost. The suite proves BOTH halves of it: the form delegates, and the
   * shared primitive declares the target.
   */
  it.each(FUENTES_DELEGADOS)(
    "%s hereda el objetivo táctil del campo compartido",
    (ruta) => {
      expect(leer(ruta)).toContain("@/components/forms/FormField");
      expect(
        readFileSync(
          join(process.cwd(), "src", "components", "forms", "FormField.tsx"),
          "utf8",
        ),
      ).toContain("min-h-11");
    },
  );
});

describe("el chip del pago es compartido, no duplicado", () => {
  it("el estado del pago delega la pintura en el chip de la zona de pagos", () => {
    expect(leer("pases/components/EstadoPagoPase.tsx")).toContain(
      "@/features/pagos/components",
    );
  });

  it("el chip compartido no conoce ningun tipo de otro dominio", () => {
    const fuente = leer("pagos/components/ChipPago.tsx");

    expect(fuente).not.toContain("@/features/pases");
    expect(fuente).not.toContain("@/features/inscripciones");
  });
});

describe("la tarjeta del pase", () => {
  it("el pase elegido queda marcado y el que no, no", async () => {
    const usuario = userEvent.setup();

    render(
      <CatalogoPases
        pases={[
          CATALOGO.pases[0],
          {
            ...CATALOGO.pases[0],
            id: "00000000-0000-4000-8000-0000000000c2",
            nombre: "PASE VIP",
          },
        ]}
      />,
    );

    const normal = screen.getByRole("button", { name: /PASE DE EJEMPLO/ });
    const vip = screen.getByRole("button", { name: /PASE VIP/ });

    expect(normal.getAttribute("aria-pressed")).toBe("false");
    expect(vip.getAttribute("aria-pressed")).toBe("false");

    await usuario.click(vip);

    expect(
      screen
        .getByRole("button", { name: /PASE VIP/ })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen
        .getByRole("button", { name: /PASE DE EJEMPLO/ })
        .getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("un pase bloqueado dice por qué y no se puede elegir", () => {
    render(
      <TarjetaPase
        pase={CATALOGO.pases[0]}
        onSelect={() => {}}
        motivoBloqueo="El inventario de este pase se agotó."
      />,
    );

    expect(
      screen.getByText("El inventario de este pase se agotó."),
    ).toBeDefined();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("la tarjeta muestra el precio que publicó el servidor y ningún total", () => {
    render(<TarjetaPase pase={CATALOGO.pases[0]} onSelect={() => {}} />);

    expect(screen.getByText("PEN 0.00")).toBeDefined();
    expect(screen.getByText("por pase")).toBeDefined();
    expect(screen.queryByText(/total/i)).toBeNull();
  });
});
