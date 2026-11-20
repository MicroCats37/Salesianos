// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EsqueletoOperativo } from "../components/EsqueletoOperativo";
import { ListaOperativa } from "../components/ListaOperativa";
import { MarcoOperativo } from "../components/MarcoOperativo";
import { VeredictoOperativo } from "../components/VeredictoOperativo";
import type {
  ColumnaOperativa,
  FilaOperativa,
  Veredicto,
} from "../types/operaciones.types";
import { rolOperativoDesdeCodigo } from "../utils/veredicto.adapter";

const COLUMNAS: ColumnaOperativa[] = [
  { key: "nombre", label: "Nombre", titular: true },
  { key: "estado", label: "Estado" },
  { key: "importe", label: "Importe", numerico: true },
];

const FILAS: FilaOperativa[] = [
  {
    id: "fila-1",
    celdas: {
      nombre: "FILA DE EJEMPLO",
      estado: "Estado de la fila",
      importe: 10,
    },
  },
];

const VERDICTO: Veredicto = {
  estado: {
    codigo: "PAGADA",
    etiqueta: "Pagada",
    descripcion: "El pago está confirmado y la compra consta como pagada.",
  },
  rol: "confirmado",
};

describe("el chip de un veredicto", () => {
  it("muestra la etiqueta del backend y NUNCA el código", () => {
    render(<VeredictoOperativo veredicto={VERDICTO} />);

    expect(screen.getByText("Pagada")).toBeDefined();
    expect(screen.queryByText("PAGADA")).toBeNull();
  });

  it("un rol desconocido se pinta de forma neutra y no rompe", () => {
    render(
      <VeredictoOperativo
        veredicto={{
          estado: {
            codigo: "CODIGO_NUEVO",
            etiqueta: "Veredicto nuevo",
            descripcion: "",
          },
          rol: "desconocido",
        }}
      />,
    );

    expect(screen.getByText("Veredicto nuevo")).toBeDefined();
  });
});

describe("el adaptador del veredicto", () => {
  it("conoce el vocabulario congelado del backend y neutraliza lo desconocido", () => {
    expect(rolOperativoDesdeCodigo("PAGADA")).toBe("confirmado");
    expect(rolOperativoDesdeCodigo("PENDIENTE")).toBe("pendiente");
    expect(rolOperativoDesdeCodigo("CANCELADA")).toBe("rechazado");
    expect(rolOperativoDesdeCodigo("CODIGO_QUE_NO_EXISTE")).toBe("desconocido");
  });
});

describe("la lista operativa", () => {
  it("sin filas muestra el estado vacío y NUNCA una tabla vacía", () => {
    render(
      <ListaOperativa
        caption="Lista de ejemplo"
        columnas={COLUMNAS}
        vacio={<p>No hay nada todavía</p>}
      />,
    );

    expect(screen.getByText("No hay nada todavía")).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("con filas publica una tabla con encabezados de columna", () => {
    render(
      <ListaOperativa
        caption="Lista de ejemplo"
        columnas={COLUMNAS}
        filas={FILAS}
      />,
    );

    expect(screen.getByRole("table")).toBeDefined();
    expect(screen.getByRole("columnheader", { name: "Nombre" })).toBeDefined();
    expect(screen.getByRole("columnheader", { name: "Importe" })).toBeDefined();
  });
});

describe("el marco de los estados", () => {
  it("sin datos muestra el estado honesto", () => {
    render(
      <MarcoOperativo
        estado={{ estado: "sin-datos" }}
        sinDatos={<p>Todavía no hay datos</p>}
        cargando={<p>Cargando</p>}
      >
        {() => <p>Contenido</p>}
      </MarcoOperativo>,
    );

    expect(screen.getByText("Todavía no hay datos")).toBeDefined();
    expect(screen.queryByText("Contenido")).toBeNull();
  });

  it("un error muestra el mensaje del backend, verbatim", () => {
    render(
      <MarcoOperativo
        estado={{
          estado: "error",
          mensaje: "La orden de pago ya fue pagada por otro canal.",
        }}
        sinDatos={<p>Todavía no hay datos</p>}
        cargando={<p>Cargando</p>}
      >
        {() => <p>Contenido</p>}
      </MarcoOperativo>,
    );

    expect(
      screen.getByText("La orden de pago ya fue pagada por otro canal."),
    ).toBeDefined();
  });

  it("sin permiso explica la falta de permiso y no propone un rodeo", () => {
    render(
      <MarcoOperativo
        estado={{ estado: "sin-permiso" }}
        sinDatos={<p>Todavía no hay datos</p>}
        cargando={<p>Cargando</p>}
      >
        {() => <p>Contenido</p>}
      </MarcoOperativo>,
    );

    expect(screen.getByText("No tienes permiso para ver esto")).toBeDefined();
    expect(screen.queryByText("Contenido")).toBeNull();
  });
});

describe("el esqueleto de la lista", () => {
  it("refleja la geometría de la lista: tarjetas y tabla", () => {
    const { container } = render(<EsqueletoOperativo columnas={COLUMNAS} />);

    expect(container.querySelector("table")).not.toBeNull();
    expect(container.querySelectorAll("ul").length).toBeGreaterThan(0);
  });
});

const FUENTES = [
  "components/BarraFiltros.tsx",
  "components/ListaOperativa.tsx",
  "components/MarcoOperativo.tsx",
  "components/VeredictoOperativo.tsx",
  "components/PaginacionOperativa.tsx",
  "components/ConfirmacionIrreversible.tsx",
];

describe("la capa operativa no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "operaciones", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("la capa operativa cumple el contrato de los cinco anchos", () => {
  it.each(FUENTES)("%s usa objetivos táctiles de 44 px", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "operaciones", ruta),
      "utf8",
    );

    expect(fuente).toContain("min-h-11");
  });
});
