"""`modules.administracion` — la capa transversal de la administración operativa.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Este módulo es un ** agregador de LECTURA**: no posee ninguno de los datos que
publica. Compone los hechos que los módulos DUEÑOS ya publican (edición,
inscripciones, equipos, participantes, cupos, pases) y los proyecta en el modelo
de lectura transversal que consume el panel:

| Pieza | Qué es |
|---|---|
| `AccionAuditada` | el ACTA de las acciones sensibles: quién, cuándo, por qué |
| `AdminResumenSelector` | los agregados de la edición (métricas e incidencias) |
| `AdminAuditoriaSelector` | la lectura del acta de auditoría |

Reglas que este módulo respeta:

- **No es dueño de ningún dato de negocio.** Lee los modelos del módulo DUEÑO
  a través de su capa `domain/models` y NO importa jamás la capa `presentation/`
  de otro módulo (`contract/api-wrapper-presenter-contract.md` §1).
- **No reimplementa reglas.** Sólo cuenta y suma hechos ya publicados. La
  regla de "quién puede", "qué es una plantilla completa" o "qué es un pago
  pendiente" vive en el módulo que posee el dato.
- **No duplica la propiedad del dataset.** El frontend tiene UN cliente por
  dataset (`features/admin/operaciones/services/admin.service.ts`) y el
  backend tiene UN presentador por forma.
- **La auditoría no expone secretos.** El acta guarda el actor, el momento y el
  motivo; el presenter publica una lista blanca de los datos y nunca el
  contenido crudo.
"""
