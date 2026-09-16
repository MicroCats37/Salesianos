// Trazabilidad visual components barrel — only public UI components exposed

export * from "./buildSolicitudFlow";
// New (2026-09-13): temporal summary strip and chronological history.
export { ChronologicalHistory } from "./ChronologicalHistory";
// U4-U6 REVERSED: CSS-only card flow (React Flow removed per user decision).
export {
  SolicitudCardFlow,
  type SolicitudCardFlowProps,
} from "./SolicitudCardFlow";
export { TemporalSummary } from "./TemporalSummary";
// U7-U8: compact inspector + single selection model.
export {
  TraceabilityInspector,
  type TraceabilityInspectorProps,
} from "./TraceabilityInspector";
export {
  TrazabilidadView,
  type TrazabilidadViewProps,
} from "./TrazabilidadView";
// U1-U2: pure traceability builders.
export * from "./traceabilityLabels";
export * from "./traceabilitySelection";
export * from "./traceabilityTimeline";
