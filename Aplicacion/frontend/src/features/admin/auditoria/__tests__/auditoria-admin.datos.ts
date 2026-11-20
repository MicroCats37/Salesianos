/**
 * The data of the ACTA of the sensitive actions.
 *
 * It is the shape the backend publishes (`AuditoriaListadoOut`), and it
 * carries the two properties that matter: the acta NAMES the actor, the
 * moment and the reason, and it does NOT carry the raw context of the
 * action.
 */
export const ACTA_DERECHA = {
  id: "00000000-0000-4000-8000-0000000000C1",
  edicion_id: "00000000-0000-4000-8000-000000000001",
  actor: "ADMINISTRADOR DE EJEMPLO",
  accion: "RETIRAR_PARTICIPANTE",
  entidad: "PARTICIPACION",
  entidad_id: "00000000-0000-4000-8000-0000000000D1",
  motivo: "El participante no pertenece a la disciplina de la edición.",
  registrado_en: "2026-01-01T00:00:00Z",
};

export const ACTA_LISTADO = {
  items: [ACTA_DERECHA],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};
