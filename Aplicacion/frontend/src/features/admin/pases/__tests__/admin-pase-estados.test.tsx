// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AvisoFalloPase } from "../components/AvisoFalloPase";
import { PanelCortesias } from "../components/PanelCortesias";
import type { EstadoListaCortesias } from "../hooks/useAdminPases";
import type { AdminCortesiaListaItem } from "../schemas/admin.pase.schema";

/** A courtesy that the padrón granted. */
const CORTESIA: AdminCortesiaListaItem = {
  id: "cortesia-1",
  derecho_id: "derecho-1",
  pase_nombre: "Pase FEST",
  edicion_nombre: "EDICION DE EJEMPLO",
  persona_nombres: "Rosa Díaz",
  persona_tipo_documento: "DNI",
  persona_numero_documento: "77777777",
  estado: "ACTIVA",
  motivo: "Cortesía de la organización.",
  actor_nombres: "Administrador",
  concedido_en: "2026-11-20T10:00:00Z",
};

/** The page of the list, with the courtesy that was granted. */
const PAGINA_DATOS = {
  items: [CORTESIA],
  total: 1,
  page: 1,
  page_size: 25,
  total_pages: 1,
};

/** The state of the list when the answer arrived. */
const PAGINA: EstadoListaCortesias = {
  estado: "listo",
  datos: PAGINA_DATOS,
};

describe("ADP — el estado de carga del panel de cortesías", () => {
  it("mientras carga, el panel dice que carga y NO inventa filas", () => {
    render(<PanelCortesias estado={{ estado: "cargando" }} />);

    expect(screen.getByText("Cargando las cortesías...")).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("ADP — el estado de error del panel de cortesías", () => {
  it("el error se anuncia con la prosa del backend", () => {
    render(
      <PanelCortesias
        estado={{
          estado: "error",
          mensaje: "No pudimos cargar las cortesías.",
        }}
      />,
    );

    const alerta = screen.getByRole("alert");
    expect(alerta.textContent).toContain("No pudimos cargar las cortesías.");
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("ADP — el estado vacío del panel de cortesías", () => {
  it("sin cortesías, el panel lo dice y NO muestra una lista inventada", () => {
    render(
      <PanelCortesias
        estado={{
          estado: "listo",
          datos: {
            items: [],
            total: 0,
            page: 1,
            page_size: 25,
            total_pages: 0,
          },
        }}
      />,
    );

    expect(
      screen.getByText("Todavía no hay cortesías registradas"),
    ).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("ADP — la lista de las cortesías", () => {
  it("cada fila dice QUIÉN, QUÉ pase, el estado y el motivo del acta", () => {
    render(<PanelCortesias estado={PAGINA} />);

    expect(screen.getByText("Rosa Díaz")).toBeDefined();
    expect(screen.getByText("Pase FEST")).toBeDefined();
    expect(screen.getByText("Activa")).toBeDefined();
    expect(screen.getByText("Cortesía de la organización.")).toBeDefined();
    expect(screen.getByText("Administrador")).toBeDefined();
  });

  it("la lista NO muestra ningún importe", () => {
    const { container } = render(<PanelCortesias estado={PAGINA} />);

    expect(container.textContent).not.toContain("S/");
    expect(container.textContent).not.toContain("PEN");
    expect(container.textContent).not.toContain("total");
  });

  it("una cortesía revocada se muestra como revocada y NO ofrece revocarla", () => {
    render(
      <PanelCortesias
        estado={{
          estado: "listo",
          datos: {
            ...PAGINA_DATOS,
            items: [{ ...CORTESIA, estado: "REVOCADA" }],
          },
        }}
      />,
    );

    expect(screen.getByText("Revocada")).toBeDefined();
    expect(screen.queryByRole("button", { name: /Revocar/ })).toBeNull();
  });

  it("la acción de revocar nombra a la persona: no hay dos botones iguales", () => {
    render(
      <PanelCortesias
        estado={PAGINA}
        onRevocar={vi.fn()}
        onEmitirCredencial={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Revocar la cortesía de Rosa Díaz",
      }),
    ).toBeDefined();
  });

  it("la credencial solo se ofrece cuando el listado publica el DERECHO", () => {
    const { rerender } = render(
      <PanelCortesias
        estado={{
          estado: "listo",
          datos: {
            ...PAGINA_DATOS,
            items: [{ ...CORTESIA, derecho_id: null }],
          },
        }}
        onEmitirCredencial={vi.fn()}
      />,
    );

    // Sin un DERECHO real NO hay credencial: el identificador ausente no se
    // inventa y la acción no se ofrece.
    expect(
      screen.queryByRole("button", { name: /Emitir la credencial/ }),
    ).toBeNull();
    expect(
      screen.getByText(/Estas cortesías no tienen un derecho asociado/),
    ).toBeDefined();

    rerender(
      <PanelCortesias
        estado={{
          estado: "listo",
          datos: {
            ...PAGINA_DATOS,
            items: [{ ...CORTESIA, derecho_id: "derecho-1" }],
          },
        }}
        onEmitirCredencial={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Emitir la credencial de Rosa Díaz",
      }),
    ).toBeDefined();
  });

  it("la acción de la credencial entrega el DERECHO de la fila", async () => {
    const alEmitir = vi.fn();

    render(
      <PanelCortesias
        estado={{
          estado: "listo",
          datos: {
            ...PAGINA_DATOS,
            items: [{ ...CORTESIA, derecho_id: "derecho-1" }],
          },
        }}
        onEmitirCredencial={alEmitir}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Emitir la credencial de Rosa Díaz",
      }),
    );

    expect(alEmitir).toHaveBeenCalledTimes(1);
    expect(alEmitir.mock.calls[0][0].derecho_id).toBe("derecho-1");
  });

  it("la tabla tiene sucaption para quien lee con un lector de pantalla", () => {
    render(<PanelCortesias estado={PAGINA} />);

    expect(
      screen.getByText("Cortesías registradas en la edición"),
    ).toBeDefined();
  });
});

describe("ADP — el aviso de un fallo", () => {
  it("el conflicto se anuncia como una alerta con la prosa del backend", () => {
    render(
      <AvisoFalloPase
        fallo={{
          tipo: "conflicto",
          titulo: "El servidor rechazó la operación",
          mensaje:
            "La persona ya tiene una entrada activa de este pase en esta edición.",
        }}
      />,
    );

    const alerta = screen.getByRole("alert");
    expect(alerta.textContent).toContain("El servidor rechazó la operación");
    expect(alerta.textContent).toContain(
      "La persona ya tiene una entrada activa de este pase en esta edición.",
    );
  });

  it("un permiso denegado se anuncia con su propio encabezado", () => {
    render(
      <AvisoFalloPase
        fallo={{
          tipo: "permiso",
          titulo: "No tienes permiso para esta operación",
          mensaje: "No tienes permiso para esta operación.",
        }}
      />,
    );

    expect(screen.getByRole("alert").textContent).toContain(
      "No tienes permiso para esta operación",
    );
  });
});
