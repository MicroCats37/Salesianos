// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdminPagosLista } from "./AdminPagosLista";

/**
 * The payments table (A5) and its drilldown (A6).
 *
 * The table used to publish THREE sibling badges — the commercial state of
 * the purchase, the state of the order and the origin of the evidence — and
 * let the reader compare them. It now publishes ONE state: the operator
 * verdict the backend computes (`estado_operativo`), with the origin of the
 * evidence as a secondary line.
 *
 * The suite pins that contract:
 *
 * 1. the row shows the verdict and the evidence, and NEVER the raw facts
 *    the verdict is made of,
 * 2. the facts stay reachable in the drilldown — they are the audit trail
 *    of the decision,
 * 3. the client NEVER recomputes the verdict: it renders the code it was
 *    given.
 */

const { CATALOGO, DETALLE, FILAS, estado } = vi.hoisted(() => {
  const primera = {
    compra_id: "11111111-1111-4111-8111-111111111111",
    orden_pago_id: "22222222-2222-4222-8222-222222222222",
    numero_orden: "OP-100",
    inscripcion_id: "33333333-3333-4333-8333-333333333333",
    pase_id: null,
    responsable_nombre: "Persona Compradora",
    tipo: "INICIAL",
    producto_nombre: "Pack FEST",
    cantidad: 2,
    precio_unitario: 75,
    total: 150,
    estado_compra: "PENDIENTE",
    estado_orden: "PAGADA",
    pagada_en: "2026-10-01T12:00:00Z",
    origen_pago: "MANUAL",
    estado_operativo: "PAGADA_SIN_LIQUIDAR",
    monto_orden: 150,
    moneda_orden: "PEN",
    beneficiarios_activos: 0,
    beneficiarios_revocados: 0,
    created_at: "2026-09-30T09:00:00Z",
  };

  const segunda = {
    ...primera,
    orden_pago_id: "44444444-4444-4444-8444-444444444444",
    numero_orden: "OP-200",
    estado_compra: "PAGADA",
    pagada_en: "2026-10-02T12:00:00Z",
    origen_pago: "SIN_PAGO",
    estado_operativo: "PAGADA_SIN_EVIDENCIA",
  };

  return {
    FILAS: [primera, segunda],
    DETALLE: {
      ...primera,
      transacciones: [],
      aprobaciones: [],
      beneficiarios: [],
    },
    CATALOGO: {
      evento_id: "55555555-5555-4555-8555-555555555555",
      evento_nombre: "FEST 2026",
      disciplinas: [],
      paquetes: [],
      promociones: [],
      categorias: [],
      puntos_acceso: ["Puerta 1"],
      estados: {
        inscripcion: ["BORRADOR", "RECIBIDA"],
        compra: ["PENDIENTE", "PAGADA", "CANCELADA"],
        orden_pago: ["PENDIENTE", "PAGADA", "CANCELADA", "VENCIDA"],
        asignacion_cupo: ["ACTIVA", "LIBERADA", "REVOCADA"],
        equipo: ["EQUIPO_ACTIVO", "EQUIPO_CANCELADO"],
        acreditacion: ["PENDIENTE", "ACTIVA"],
        autorizacion_fiesta: ["AUTOMATICA", "AUTORIZADA", "BLOQUEADA"],
        acceso: ["PERMITIDO", "DENEGADO"],
        pool: ["LISTO", "ESPERANDO_PAGO"],
        rol_participante: ["J", "C", "D"],
        roster: ["COMPLETO", "INCOMPLETO"],
        estado_participacion: ["A", "R"],
        tipo_compra: ["INICIAL", "AMPLIACION", "PASE"],
        estado_operativo_pago: [
          "SIN_ORDEN",
          "PAGADA",
          "PAGADA_SIN_LIQUIDAR",
          "PAGADA_SIN_EVIDENCIA",
          "PAGADA_SIN_FECHA",
          "PENDIENTE",
          "CANCELADA",
          "VENCIDA",
        ],
      },
    },
    estado: { detalleId: "" },
  };
});

vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/pagos",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../hooks/useAdminControlLista", () => ({
  useAdminControlLista: () => ({
    estado: { page: 1, pageSize: 25, q: "", ordering: "", filtros: {} },
    hayFiltros: false,
    contadorFiltros: 0,
    onBuscar: vi.fn(),
    onCambiarOrden: vi.fn(),
    onCambiarPagina: vi.fn(),
    onCambiarPageSize: vi.fn(),
    onLimpiarFiltros: vi.fn(),
    onFiltro: vi.fn(),
    onFiltros: vi.fn(),
  }),
}));

vi.mock("../hooks/useAdminListaUrl", () => ({
  useAdminDetalleUrl: () => ({
    detalleId: estado.detalleId,
    abrirDetalle: vi.fn(),
    cerrarDetalle: vi.fn(),
  }),
}));

vi.mock("../hooks/useAdminCatalogos", () => ({
  useAdminCatalogos: () => ({
    data: { success: true, data: CATALOGO, error: null, message: null },
    isPending: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../hooks/useAdminPagos", () => ({
  useAdminPagos: () => ({
    data: {
      success: true,
      data: {
        items: FILAS,
        total: FILAS.length,
        page: 1,
        page_size: 25,
        total_pages: 1,
      },
      error: null,
      message: null,
    },
    isPending: false,
    error: null,
    refetch: vi.fn(),
  }),
  useAdminPagoDetalle: () => ({
    data: { success: true, data: DETALLE, error: null, message: null },
    isPending: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../hooks/useAdminSession", () => ({
  useAdminTieneCapacidad: () => false,
}));

vi.mock("../pases/components", () => ({
  AdminPaseCancelarDialog: () => null,
}));

function renderizar(ui: ReactElement) {
  const cliente = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={cliente}>{ui}</QueryClientProvider>,
  );
}

/** The rows of the table, without the header. */
function filasDeDatos() {
  const filas = screen.getAllByRole("row");

  return filas.slice(1);
}

describe("AdminPagosLista — el estado del pago", () => {
  beforeEach(() => {
    estado.detalleId = "";
  });

  it("muestra UN veredicto por fila, con la evidencia debajo", () => {
    renderizar(<AdminPagosLista />);

    const [primera, segunda] = filasDeDatos();

    expect(within(primera).getByText("Pagada sin liquidar")).toBeTruthy();
    expect(within(primera).getByText("Evidencia: Manual")).toBeTruthy();

    expect(within(segunda).getByText("Pagada sin evidencia")).toBeTruthy();
    expect(within(segunda).getByText("Evidencia: Sin evidencia")).toBeTruthy();
  });

  it("NO vuelve a mostrar los hechos que el veredicto ya encarna", () => {
    renderizar(<AdminPagosLista />);

    const [primera] = filasDeDatos();

    // El estado de la compra y el de la orden ya NO compiten con el
    // veredicto: viajan en el detalle, no en la lista.
    expect(within(primera).queryByText("Pendiente")).toBeNull();
    expect(within(primera).queryByText("Pagada")).toBeNull();
  });

  it("deja de publicar las tres columnas que competian", () => {
    renderizar(<AdminPagosLista />);

    expect(screen.getByText("Estado del pago")).toBeTruthy();
    expect(screen.queryByText("Estado compra")).toBeNull();
    expect(screen.queryByText("Estado orden")).toBeNull();
    expect(screen.queryByText("Origen")).toBeNull();
  });

  it("el detalle conserva los hechos y marca la discrepancia", async () => {
    estado.detalleId = "22222222-2222-4222-8222-222222222222";

    renderizar(<AdminPagosLista />);

    // El drilldown se consulta dentro del dialogo: los filtros de la
    // toolbar se llaman igual y no deben confundirse con sus hechos.
    const dialogo = await screen.findByRole("dialog");

    expect(within(dialogo).getByText("Evidencia y estados")).toBeTruthy();

    // Los hechos del veredicto siguen siendo visibles.
    expect(within(dialogo).getByText("Estado de la compra")).toBeTruthy();
    expect(within(dialogo).getByText("Pendiente")).toBeTruthy();
    expect(within(dialogo).getByText("Estado de la orden")).toBeTruthy();
    expect(within(dialogo).getByText("Pagada")).toBeTruthy();
    expect(within(dialogo).getByText("Evidencia")).toBeTruthy();
    expect(within(dialogo).getByText("Manual")).toBeTruthy();
    expect(within(dialogo).getByText("Fecha de pago")).toBeTruthy();

    // El marcador lo decide el VEREDICTO del backend.
    expect(
      within(dialogo).getByText(
        "La orden está pagada pero la compra no está liquidada: los derechos todavía no se activaron.",
      ),
    ).toBeTruthy();
  });
});
