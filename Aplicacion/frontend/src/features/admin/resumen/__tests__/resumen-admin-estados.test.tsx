import { describe, expect, it, vi } from "vitest";
import {
  ErrorRutaAdminNoRegistrada,
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { apiSend } from "@/lib/api";
import { resumenOperativoEnvelope } from "../schemas/resumen-admin.schema";
import { RESUMEN_DERECHO, RESUMEN_IZQUIERDO } from "./resumen-admin.datos";

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

/**
 * XCT-02: the transversal summary of the administration area.
 *
 * What this suite freezes:
 *
 * - the route declares its REGISTRATION TRUTH and its reason;
 * - a forced read of a route that does not exist emits ZERO requests;
 * - the mirror accepts the published contract and rejects a foreign shape;
 * - the surface shows the HONEST state while the route does not exist;
 * - every issue carries the FILTERED drilldown that the backend published.
 */
describe("XCT-02: el resumen transversal del panel", () => {
  it("la ruta declara su verdad de registro y su motivo", () => {
    expect(RUTAS_ADMIN.resumen.ledger).toBe("RT-ADM-01");
    expect(RUTAS_ADMIN.resumen.ruta).toBe("/administracion/resumen");
    expect(RUTAS_ADMIN.resumen.registrado).toBe(false);
    expect(RUTAS_ADMIN.resumen.motivo).toBeTruthy();
    expect(RUTAS_ADMIN.resumen.permiso).toBeTruthy();
  });

  it("una lectura forzada del resumen NO emite ninguna petición", async () => {
    await expect(
      pedirAdmin(RUTAS_ADMIN.resumen, resumenOperativoEnvelope),
    ).rejects.toBeInstanceOf(ErrorRutaAdminNoRegistrada);

    expect(apiSend).not.toHaveBeenCalled();
  });

  it("el espejo acepta el contrato publicado y rechaza una forma ajena", () => {
    const envelope = {
      success: true,
      data: RESUMEN_DERECHO,
      error: null,
      message: null,
    };

    expect(resumenOperativoEnvelope.safeParse(envelope).success).toBe(true);
    expect(
      resumenOperativoEnvelope.safeParse({
        success: true,
        data: { edicion_id: 1 },
        error: null,
        message: null,
      }).success,
    ).toBe(false);
  });

  it("la superficie muestra el estado honesto mientras la ruta no existe", () => {
    const estado = estadoDesdeConsulta(
      { isPending: false, isError: false, data: undefined, error: undefined },
      RUTAS_ADMIN.resumen.registrado,
    );

    expect(estado.estado).toBe("sin-datos");
  });

  it("cada incidencia lleva la acción con el drilldown filtrado", () => {
    const incidencia = RESUMEN_IZQUIERDO.incidencias[0];

    expect(incidencia.cantidad).toBe(3);
    expect(incidencia.accion.href).toBe(
      "/administracion/inscripciones?estado_pago=PENDIENTE",
    );
  });

  it("el cliente del resumen es UNO: el del área administrativa", () => {
    expect(RUTAS_ADMIN.resumen.metodo).toBe("get");
    expect(RUTAS_ADMIN.auditoria.registrado).toBe(false);
  });
});
