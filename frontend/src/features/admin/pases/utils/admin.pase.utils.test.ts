import { describe, expect, it } from "vitest";
import {
  ADMIN_BENEFICIARIO_ACTIVA,
  ADMIN_BENEFICIARIO_REVOCADA,
  adminBeneficiarioEstadoLabel,
  adminBeneficiarioEstadoTone,
  adminPaseCancelable,
  adminPaseCancelacionAviso,
  adminPaseConteosTexto,
} from "./admin.pase.utils";

/**
 * The tests of the administrative rules of the party passes.
 *
 * The module under test is dependency-free on purpose, so the rules can be
 * verified without the React/axios runtime.
 */

describe("admin.pase · estado del derecho", () => {
  it("un derecho activo se presenta como activo", () => {
    expect(adminBeneficiarioEstadoTone(ADMIN_BENEFICIARIO_ACTIVA)).toBe(
      "emerald",
    );
    expect(adminBeneficiarioEstadoLabel(ADMIN_BENEFICIARIO_ACTIVA)).toBe(
      "Activo",
    );
  });

  it("un derecho revocado se presenta como revocado", () => {
    expect(adminBeneficiarioEstadoTone(ADMIN_BENEFICIARIO_REVOCADA)).toBe(
      "red",
    );
    expect(adminBeneficiarioEstadoLabel(ADMIN_BENEFICIARIO_REVOCADA)).toBe(
      "Revocado",
    );
  });

  it("un estado desconocido NUNCA se presenta como activo", () => {
    expect(adminBeneficiarioEstadoTone("INVENTADO")).toBe("red");
  });
});

describe("admin.pase · cancelabilidad", () => {
  it("una compra pendiente se puede cancelar", () => {
    expect(adminPaseCancelable("PENDIENTE", "PENDIENTE")).toBe(true);
  });

  it("una compra pagada se puede cancelar", () => {
    expect(adminPaseCancelable("PAGADA", "PAGADA")).toBe(true);
  });

  it("una compra ya cancelada NO se puede volver a cancelar", () => {
    expect(adminPaseCancelable("CANCELADA", "CANCELADA")).toBe(false);
  });

  it("una orden cancelada o vencida cierra la cancelación", () => {
    expect(adminPaseCancelable("PENDIENTE", "CANCELADA")).toBe(false);
    expect(adminPaseCancelable("PENDIENTE", "VENCIDA")).toBe(false);
  });
});

describe("admin.pase · conteos de los derechos", () => {
  it("los derechos activos y revocados se reportan SEPARADOS", () => {
    expect(adminPaseConteosTexto(2, 1)).toBe("2 activo(s) · 1 revocado(s)");
  });

  it("un lote sin derechos reporta cero de los dos", () => {
    expect(adminPaseConteosTexto(0, 0)).toBe("0 activo(s) · 0 revocado(s)");
  });
});

describe("admin.pase · aviso de cancelación", () => {
  it("el aviso NUNCA promete un reembolso", () => {
    const aviso = adminPaseCancelacionAviso().toLowerCase();
    expect(aviso).toContain("no devuelve dinero");
    expect(aviso).not.toContain("reembols");
  });
});
