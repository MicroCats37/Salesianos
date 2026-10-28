import { describe, expect, it } from "vitest";
import type {
  PaseBeneficiarioAuditado,
  PaseConteosBeneficiarios,
} from "../schemas/pase.beneficiario.schema";
import type { PersonaResuelta } from "../schemas/persona.schema";
import {
  BENEFICIARIO_ACTIVA,
  BENEFICIARIO_REVOCADA,
  paseAsignacionAbierta,
  paseBeneficiarioEstadoLabel,
  paseBeneficiarioTone,
  pasePersonaYaSeleccionada,
  pasePuedeAsignar,
  paseSlotsLibres,
  paseSlotsResumen,
  paseSlotsUsados,
} from "./pase.beneficiario";

/**
 * The tests of the nominative rights of a pass.
 *
 * The module under test is dependency-free on purpose, so the rules can be
 * verified without the React/axios runtime.
 */

/** One right of a batch. */
function beneficiario(
  personaId: string,
  slot: number,
  estado = BENEFICIARIO_ACTIVA,
): PaseBeneficiarioAuditado {
  return {
    persona_id: personaId,
    nombre_completo: `Persona ${personaId}`,
    tipo_documento: "DNI",
    numero_documento: `1000000${slot}`,
    slot,
    estado,
    asignado_en: "2026-10-28T10:00:00",
    revocado_en:
      estado === BENEFICIARIO_REVOCADA ? "2026-10-29T10:00:00" : null,
    motivo_revocacion:
      estado === BENEFICIARIO_REVOCADA ? "Error de asignación" : null,
  };
}

/** The immutable slot accounting of a batch of three passes. */
function conteos(
  overrides: Partial<PaseConteosBeneficiarios> = {},
): PaseConteosBeneficiarios {
  return {
    cantidad_pases: 3,
    activos: 2,
    revocados: 0,
    slots_usados: 2,
    slots_disponibles: 1,
    ...overrides,
  };
}

describe("pase.beneficiario · estado del derecho", () => {
  it("un derecho activo se presenta como activo", () => {
    expect(paseBeneficiarioTone(BENEFICIARIO_ACTIVA)).toBe("activa");
    expect(paseBeneficiarioEstadoLabel(BENEFICIARIO_ACTIVA)).toBe("Activo");
  });

  it("un derecho revocado se presenta como revocado", () => {
    expect(paseBeneficiarioTone(BENEFICIARIO_REVOCADA)).toBe("revocada");
    expect(paseBeneficiarioEstadoLabel(BENEFICIARIO_REVOCADA)).toBe("Revocado");
  });

  it("un estado desconocido NUNCA se presenta como activo", () => {
    expect(paseBeneficiarioTone("INVENTADO")).toBe("revocada");
  });
});

describe("pase.beneficiario · slots inmutables", () => {
  it("los slots usados incluyen los revocados", () => {
    const usados = paseSlotsUsados([
      beneficiario("p1", 3),
      beneficiario("p2", 1, BENEFICIARIO_REVOCADA),
    ]);
    expect(usados).toEqual([1, 3]);
  });

  it("los slots libres son los más bajos que quedan", () => {
    const libres = paseSlotsLibres(4, [
      beneficiario("p1", 1),
      beneficiario("p2", 3),
    ]);
    expect(libres).toEqual([2, 4]);
  });

  it("un slot revocado NUNCA vuelve a estar libre", () => {
    const libres = paseSlotsLibres(3, [
      beneficiario("p1", 1),
      beneficiario("p2", 2, BENEFICIARIO_REVOCADA),
    ]);
    expect(libres).toEqual([3]);
  });

  it("un lote sin derechos tiene todos los slots libres", () => {
    expect(paseSlotsLibres(3, [])).toEqual([1, 2, 3]);
  });
});

describe("pase.beneficiario · resumen de la contabilidad", () => {
  it("el resumen reproduce los conteos del backend", () => {
    expect(paseSlotsResumen(conteos())).toEqual({
      total: 3,
      activos: 2,
      revocados: 0,
      usados: 2,
      disponibles: 1,
    });
  });
});

describe("pase.beneficiario · asignación", () => {
  it("una selección que cabe en los slots libres se acepta", () => {
    expect(pasePuedeAsignar(conteos(), 1)).toBe(true);
  });

  it("una selección que excede los slots libres se rechaza", () => {
    expect(pasePuedeAsignar(conteos(), 2)).toBe(false);
  });

  it("una selección vacía nunca se envía", () => {
    expect(pasePuedeAsignar(conteos(), 0)).toBe(false);
  });

  it("un lote sin slots libres está cerrado", () => {
    expect(paseAsignacionAbierta(conteos({ slots_disponibles: 0 }))).toBe(
      false,
    );
  });
});

describe("pase.beneficiario · selección de personas", () => {
  const persona = (personaId: string): PersonaResuelta => ({
    persona_id: personaId,
    nombre_completo: "Persona Prueba",
    tipo_documento: "DNI",
    numero_documento: "12345678",
  });

  it("una persona ya seleccionada NO se puede volver a añadir", () => {
    const personas = [persona("p1"), persona("p2")];

    expect(pasePersonaYaSeleccionada(personas, "p1")).toBe(true);
    expect(pasePersonaYaSeleccionada(personas, "p2")).toBe(true);
  });

  it("una persona nueva SÍ se puede añadir", () => {
    const personas = [persona("p1")];

    expect(pasePersonaYaSeleccionada(personas, "p2")).toBe(false);
  });

  it("una selección vacía admite cualquier persona", () => {
    expect(pasePersonaYaSeleccionada([], "p1")).toBe(false);
  });
});
