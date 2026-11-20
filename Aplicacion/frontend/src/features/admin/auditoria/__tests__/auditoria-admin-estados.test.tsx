import { describe, expect, it, vi } from "vitest";
import {
  ErrorRutaAdminNoRegistrada,
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { apiSend } from "@/lib/api";
import { auditoriaListadoEnvelope } from "../schemas/auditoria-admin.schema";
import { ACTA_DERECHA, ACTA_LISTADO } from "./auditoria-admin.datos";

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

/**
 * XCT-02 (work unit 2): the acta of the sensitive actions.
 *
 * What this suite freezes:
 *
 * - the route declares its REGISTRATION TRUTH and its reason;
 * - a forced read of the acta emits ZERO requests;
 * - the mirror accepts the published contract and rejects a foreign shape;
 * - the mirror REJECTS a raw context: the acta publishes a white list;
 * - the surface shows the HONEST state while the route does not exist;
 * - the acta NAMES the actor, the moment and the reason.
 */
describe("XCT-02: el acta transversal de las acciones sensibles", () => {
  it("la ruta declara su verdad de registro y su motivo", () => {
    expect(RUTAS_ADMIN.auditoria.ledger).toBe("RT-ADM-02");
    expect(RUTAS_ADMIN.auditoria.ruta).toBe("/administracion/auditoria");
    expect(RUTAS_ADMIN.auditoria.registrado).toBe(false);
    expect(RUTAS_ADMIN.auditoria.motivo).toBeTruthy();
    expect(RUTAS_ADMIN.auditoria.permiso).toBeTruthy();
  });

  it("una lectura forzada del acta NO emite ninguna petición", async () => {
    await expect(
      pedirAdmin(RUTAS_ADMIN.auditoria, auditoriaListadoEnvelope),
    ).rejects.toBeInstanceOf(ErrorRutaAdminNoRegistrada);

    expect(apiSend).not.toHaveBeenCalled();
  });

  it("el espejo acepta el contrato publicado y rechaza una forma ajena", () => {
    const envelope = {
      success: true,
      data: ACTA_LISTADO,
      error: null,
      message: null,
    };

    expect(auditoriaListadoEnvelope.safeParse(envelope).success).toBe(true);
    expect(
      auditoriaListadoEnvelope.safeParse({
        success: true,
        data: { items: [{ id: 1 }], total: 1 },
        error: null,
        message: null,
      }).success,
    ).toBe(false);
  });

  it("el espejo RECHAZA un acta con el contexto crudo", () => {
    const envelope = {
      success: true,
      data: {
        ...ACTA_LISTADO,
        items: [{ ...ACTA_DERECHA, contexto: { password: "secreto" } }],
      },
      error: null,
      message: null,
    };

    expect(auditoriaListadoEnvelope.safeParse(envelope).success).toBe(false);
  });

  it("la superficie muestra el estado honesto mientras la ruta no existe", () => {
    const estado = estadoDesdeConsulta(
      { isPending: false, isError: false, data: undefined, error: undefined },
      RUTAS_ADMIN.auditoria.registrado,
    );

    expect(estado.estado).toBe("sin-datos");
  });

  it("el acta nombra actor, momento, acción y motivo", () => {
    expect(ACTA_DERECHA.actor).toBeTruthy();
    expect(ACTA_DERECHA.registrado_en).toBeTruthy();
    expect(ACTA_DERECHA.accion).toBe("RETIRAR_PARTICIPANTE");
    expect(ACTA_DERECHA.motivo).toBeTruthy();
  });
});
