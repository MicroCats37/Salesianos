"""Módulo de VALIDACIONES: la credencial, su vista previa y su canje.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-RT-1.0.0` · `FR-05` (ciclo de vida de derechos)

Este módulo es el SERVICIO COMÚN de control de acceso y de entrega
(`funcional/01` §1). **NO** concede derechos, **NO** reimplementa reglas del
dominio y **NO** duplica el derecho: sólo lo referencia, lo consulta a su
módulo dueño y registra el consumo.

Las tres prohibiciones congeladas (`FR-05` §1) travelan con el módulo:

1. `validaciones` NO crea, concede ni modifica derechos: consulta al dueño.
2. El `Ticket` NO duplica el derecho: es una credencial que lo REFERENCIA.
3. El `Ticket` NO es un permiso Django: el grupo autoriza a OPERAR; el
   derecho autoriza a INGRESAR o CANJEAR (`contratos/02` §6).

La ruta de un permiso NO es una credencial de asistencia: el DNI nunca abre
una puerta (`RN-U04`).
"""

default_app_config = "modules.validaciones.apps.ValidacionesConfig"
