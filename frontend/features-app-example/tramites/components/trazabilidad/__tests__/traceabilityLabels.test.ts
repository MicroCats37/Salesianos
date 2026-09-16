/**
 * Unit tests for traceabilityLabels — runnable today with the repo's Node 22
 * via the tsc-compile verification documented in the apply-progress.
 * Zero-dependency: uses node:test + node:assert (built into Node).
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  eventoTipoLabel,
  humanizeEnum,
  participacionLabel,
  periodoEstadoLabel,
  respuestaEstadoLabel,
  respuestaLabel,
  solicitudEstadoLabel,
  tipoCierreLabel,
} from "../traceabilityLabels";

describe("traceabilityLabels", () => {
  describe("humanizeEnum", () => {
    it("never leaks snake_case for unknown values", () => {
      assert.equal(humanizeEnum("ESTADO_EXTRA"), "Estado extra");
      assert.equal(humanizeEnum("MI_EVENTO_RARO"), "Mi evento raro");
      assert.ok(!humanizeEnum("ALGO_SNEAKY").includes("_"));
    });

    it("handles null, empty and whitespace", () => {
      assert.equal(humanizeEnum(null), "Sin dato");
      assert.equal(humanizeEnum(undefined), "Sin dato");
      assert.equal(humanizeEnum(""), "Sin dato");
      assert.equal(humanizeEnum("   "), "Sin dato");
    });

    it("collapses duplicate separators", () => {
      assert.equal(humanizeEnum("EN__GESTION"), "En gestion");
    });
  });

  describe("known enum mappings", () => {
    it("global solicitud states", () => {
      assert.equal(solicitudEstadoLabel("REGISTRADA"), "Registrada");
      assert.equal(solicitudEstadoLabel("EN_GESTION"), "En Gestión");
      assert.equal(solicitudEstadoLabel("FINALIZADA"), "Finalizada");
      assert.equal(solicitudEstadoLabel("ANULADA"), "Anulada");
      assert.equal(solicitudEstadoLabel("NO_EXISTE"), "No existe");
    });

    it("period states", () => {
      assert.equal(periodoEstadoLabel("PENDIENTE"), "Pendiente");
      assert.equal(periodoEstadoLabel("EN_GESTION"), "En Gestión");
      assert.equal(periodoEstadoLabel("CERRADO"), "Cerrado");
    });

    it("participation types", () => {
      assert.equal(participacionLabel("PRINCIPAL"), "Principal");
      assert.equal(participacionLabel("ADJUNTA"), "Adjunta");
      assert.equal(participacionLabel("PRINCIPAL2"), "Principal2");
    });

    it("response types", () => {
      assert.equal(respuestaLabel("INFORME"), "Informe");
      assert.equal(respuestaLabel("OBSERVACION"), "Observación");
      assert.equal(respuestaLabel("CONFORMIDAD"), "Conformidad");
      assert.equal(respuestaLabel("DESCARGO"), "Descargo");
      assert.equal(respuestaLabel("OTRO"), "Otro");
      assert.equal(respuestaLabel("DESCONOCIDO"), "Desconocido");
    });

    it("response states", () => {
      assert.equal(respuestaEstadoLabel("BORRADOR"), "Borrador");
      assert.equal(respuestaEstadoLabel("EMITIDA"), "Emitida");
      assert.equal(respuestaEstadoLabel("ANULADA"), "Anulada");
      assert.equal(respuestaEstadoLabel("RECTIFICADA"), "Rectificada");
    });

    it("event types (canonical + alias spellings)", () => {
      assert.equal(
        eventoTipoLabel("ESTADO_SOLICITUD"),
        "Estado de la solicitud",
      );
      assert.equal(eventoTipoLabel("AREA_INCORPORADA"), "Área incorporada");
      assert.equal(eventoTipoLabel("PERIODO_INICIADO"), "Ciclo iniciado");
      assert.equal(eventoTipoLabel("PERIODO_CERRADO"), "Ciclo cerrado");
      assert.equal(
        eventoTipoLabel("PARTICIPANTE_AGREGADO"),
        "Participante agregado",
      );
      assert.equal(
        eventoTipoLabel("PARTICIPANTE_RETIRO"),
        "Participante retirado",
      );
      assert.equal(eventoTipoLabel("RESPUESTA_EMITIDA"), "Respuesta emitida");
      // Forward-compatible aliases.
      assert.equal(
        eventoTipoLabel("ESTADO_SOLICITUD_CAMBIADO"),
        "Estado de la solicitud",
      );
      assert.equal(
        eventoTipoLabel("ESTADO_PERIODO_CAMBIADO"),
        "Cambio de estado del ciclo",
      );
      assert.equal(
        eventoTipoLabel("RESPUESTA_REGISTRADA"),
        "Respuesta registrada",
      );
      // Unknown → humanized, never snake_case.
      assert.equal(eventoTipoLabel("EVENTO_FUTURO"), "Evento futuro");
    });

    it("closure types", () => {
      assert.equal(tipoCierreLabel("FINALIZADO"), "Finalizado");
      assert.equal(tipoCierreLabel("DERIVADO"), "Derivado");
      assert.equal(tipoCierreLabel("RETIRADO"), "Retirado");
      assert.equal(tipoCierreLabel("RECHAZADO"), "Rechazado");
      assert.equal(tipoCierreLabel("ANULADO"), "Anulado");
      assert.equal(tipoCierreLabel("ASIGNACION_ERRONEA"), "Asignación errónea");
      assert.equal(
        tipoCierreLabel("CAMBIO_PARTICIPACION"),
        "Cambio de participación",
      );
      assert.equal(tipoCierreLabel("DESCONOCIDO"), "Desconocido");
    });
  });
});
