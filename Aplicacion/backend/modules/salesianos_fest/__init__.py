"""Módulo `salesianos_fest` — inscripciones deportivas y su catálogo.

Packet: `DOM-01` (`wave-02-domain-backend`) · Change: `salesianos-fest-rebuild`

Este módulo es el dueño del **catálogo de inscripción por edición** y de la
**inscripción inicial** del responsable:

- `Disciplina`, `Paquete`, `PaqueteBeneficio`, `PaquetePrecio` — el catálogo
  real, con alcance por EDICIÓN (`RN-E01`) y sin precio de invención.
- `Inscripcion`, `Equipo` — la inscripción del responsable y sus equipos.

Lo que este módulo NO hace:

- No cobra: la compra la crea `commerce` a través del puerto congelado
  `CompraFlujo` (`RN-C01`, `FREEZE-CM-1.0.0`).
- No habilita cupos: la activación de derechos es de `DOM-02`
  (`RN-I02`: una compra pendiente NO habilita cupos).
- No decide elegibilidad de participantes: es de `DOM-02`.
- No inventa precios: un paquete sin precio vigente no está a la venta.

`SCHEMA_VERSION` es un REGISTRO, no un campo del wire (`FR-07` §1.1).
"""

#: Versión congelada del contrato de presenters/schemas del módulo.
SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
