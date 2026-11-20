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
#:
#: DOM-03 (2026-11-19) — ESTA COPIA ERA UNA SEGUNDA FUENTE DE VERDAD. El
#: paquete declaraba aquí un literal (`1.0.0`) mientras la fuente canónica
#: (`modules.salesianos_fest.presentation.schemas.SCHEMA_VERSION`) ya valía
#: `1.1.0` (DOM-02) y `1.2.0` (DOM-03). Dos literales para el MISMO
#: contrato congelado es exactamente el drift que `FR-07` §1.1 mete en
#: existir: el que se lea por el nombre corto del paquete leería una versión
#: equivocada sin ningún aviso.
#:
#: Ahora este nombre es una REEXPORTACIÓN de la fuente canónica: hay un solo
#: literal en el módulo. `from modules.salesianos_fest import SCHEMA_VERSION`
#: sigue funcionando y devuelve el valor correcto.
#:
#: `modules/marketplace`, `modules/competencias` y `modules/patrocinadores`
#: NO declaran una copia en la raíz del paquete: éste era el único módulo con
#: dos literales.
from modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION"]
