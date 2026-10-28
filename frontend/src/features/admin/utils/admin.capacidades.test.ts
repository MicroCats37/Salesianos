import { describe, expect, it } from "vitest";
import {
  ADMIN_CAPACIDADES,
  ADMIN_NIVELES,
  adminNivelLabel,
  adminTieneCapacidad,
} from "./admin.capacidades";

/**
 * Focused tests of the capability vocabulary of the administration area.
 *
 * The module is the CLIENT mirror of `backend/core/capacidades.py`: it
 * NAMES the capabilities the backend publishes in `GET /api/auth/me`. It
 * never decides anything: the backend re-evaluates the capability on every
 * request.
 */

describe("admin.capacidades — vocabulario", () => {
  it("espeja los códigos del backend", () => {
    expect(ADMIN_CAPACIDADES.ADMIN_VER).toBe("admin.ver");
    expect(ADMIN_CAPACIDADES.PAGOS_VER).toBe("admin.pagos.ver");
    expect(ADMIN_CAPACIDADES.PAGOS_APROBAR).toBe("admin.pagos.aprobar");
    expect(ADMIN_CAPACIDADES.USUARIOS_VER).toBe("admin.usuarios.ver");
    expect(ADMIN_CAPACIDADES.USUARIOS_GESTIONAR).toBe(
      "admin.usuarios.gestionar",
    );
  });

  it("espeja los niveles del backend", () => {
    expect(ADMIN_NIVELES.USUARIO).toBe("usuario");
    expect(ADMIN_NIVELES.STAFF).toBe("staff");
    expect(ADMIN_NIVELES.SUPERUSUARIO).toBe("superusuario");
  });
});

describe("admin.capacidades — comprobación", () => {
  it("reconoce una capacidad concedida", () => {
    expect(
      adminTieneCapacidad(["admin.ver", "admin.pagos.ver"], "admin.ver"),
    ).toBe(true);
  });

  it("rechaza una capability no concedida", () => {
    expect(adminTieneCapacidad(["admin.ver"], "admin.pagos.aprobar")).toBe(
      false,
    );
  });

  it("falla cerrado sin conjunto de capacidades", () => {
    expect(adminTieneCapacidad(undefined, "admin.ver")).toBe(false);
    expect(adminTieneCapacidad(null, "admin.ver")).toBe(false);
    expect(adminTieneCapacidad([], "admin.ver")).toBe(false);
  });
});

describe("admin.capacidades — etiqueta del nivel", () => {
  it("nombra cada nivel", () => {
    expect(adminNivelLabel(ADMIN_NIVELES.SUPERUSUARIO)).toBe("Superusuario");
    expect(adminNivelLabel(ADMIN_NIVELES.STAFF)).toBe("Staff");
    expect(adminNivelLabel(ADMIN_NIVELES.USUARIO)).toBe("Participante");
  });

  it("cae en Participante ante un nivel desconocido", () => {
    expect(adminNivelLabel("inventado")).toBe("Participante");
    expect(adminNivelLabel(undefined)).toBe("Participante");
  });
});
