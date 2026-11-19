"""Vocabulario cerrado del módulo `salesianos_fest`.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Vocabularios cerrados (regla de `contract/django-app-architecture-contract.md`
§5 y §10):

1. `EstadoDisciplina` — `ACTIVA` / `INACTIVA`. Sólo una disciplina `ACTIVA`
   puede entrar en un equipo (`RN-I05`: la elegibilidad se verifica en
   backend).
2. `EstadoPaquete` — `VIGENTE` / `RETIRADO`. Un paquete `RETIRADO` no se
   ofrece ni se compra: el catálogo histórico se conserva.
3. `TipoBeneficioPaquete` — `FIJO_INICIAL` / `POR_CUPO`. Es el vocabulario de
   `RN-I06`: comprar cupos extra NO duplica los beneficios `FIJO_INICIAL`.
   La regla completa de cálculo por tipo sigue ABIERTA (`PD-09`): este módulo
   DECLARA el beneficio, no lo reparte.
4. `EstadoInscripcion` — `CREADA` / `CANCELADA`.
5. `EstadoEquipo` — `ACTIVO` / `RETIRADO`.
6. `ModalidadDisciplina` — `MIXTO` / `FEMENINO` / `MASCULINO`.
7. `CausaOperativaInscripcion` — la CAUSA OPERATIVA que el presenter publica:
   por qué la operación devolvió lo que devolvió (`RN-C07`: el comprador ve
   "pago pendiente", no "liquidación").

Packet `DOM-02` añade:

8. `EstadoParticipacion` — `ACTIVA` / `RETIRADA`. Una participación `ACTIVA`
   ocupa **un** cupo de la inscripción; una `RETIRADA` lo libera sin tocar
   la compra (`RN-I04`).
9. `RolParticipante` — `JUGADOR` / `CAPITAN` / `DELEGADO`.
10. `TipoActivacionCapacidad` — `INICIAL` / `EXPANSION`. Distingue la
    activación del ALTA de la activación de una AMPLIACIÓN: sólo la primera
    concede los beneficios `FIJO_INICIAL` (`RN-I06`).
11. `CausaOperativaPool` y `CausaOperativaCompraCupos` — las causas
    operativas que los presenters publican del pool y de la ampliación.

Este archivo NO declara precios, ni reglas de elegibilidad, ni la regla de
reparto de beneficios `POR_CUPO` (sigue ABIERTA: `PD-09`).
"""

from django.db import models


class EstadoDisciplina(models.TextChoices):
    """Estado de una disciplina dentro de su edición."""

    ACTIVA = "ACTIVA", "Activa"
    INACTIVA = "INACTIVA", "Inactiva"


class EstadoPaquete(models.TextChoices):
    """Estado comercial de un paquete dentro de su edición."""

    VIGENTE = "VIGENTE", "Vigente"
    RETIRADO = "RETIRADO", "Retirado"


class TipoBeneficioPaquete(models.TextChoices):
    """Tipo del beneficio ofrecido por un paquete (`RN-I06`, `PD-09`)."""

    FIJO_INICIAL = "FIJO_INICIAL", "Fijo inicial"
    POR_CUPO = "POR_CUPO", "Por cupo"


class EstadoInscripcion(models.TextChoices):
    """Estado de la inscripción del responsable."""

    CREADA = "CREADA", "Creada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoEquipo(models.TextChoices):
    """Estado del equipo dentro de una inscripción."""

    ACTIVO = "ACTIVO", "Activo"
    RETIRADO = "RETIRADO", "Retirado"


class ModalidadDisciplina(models.TextChoices):
    """Modalidad de la disciplina (compatibilidad de género)."""

    MIXTO = "MIXTO", "Mixto"
    FEMENINO = "FEMENINO", "Femenino"
    MASCULINO = "MASCULINO", "Masculino"


class CausaOperativaInscripcion(models.TextChoices):
    """Causa operativa de la inscripción inicial.

    Es la diferencia entre "la acabo de crear" y "ya existía y la reutilicé".
    La publica el PRESENTER: el controller no decide causas (`RN-A02`).
    """

    INSCRIPCION_CREADA = "INSCRIPCION_CREADA", "Inscripción creada"
    INSCRIPCION_REUTILIZADA = "INSCRIPCION_REUTILIZADA", "Inscripción ya existente"


class EstadoParticipacion(models.TextChoices):
    """Estado de una participación dentro del pool de una inscripción.

    `ACTIVA` ocupa un cupo; `RETIRADA` lo libera. Retirar NO anula la compra
    ni devuelve dinero (`RN-I04`): sólo devuelve el cupo al pool de ESA
    inscripción.
    """

    ACTIVA = "ACTIVA", "Activa"
    RETIRADA = "RETIRADA", "Retirada"


class RolParticipante(models.TextChoices):
    """Rol del participante dentro del equipo."""

    JUGADOR = "JUGADOR", "Jugador"
    CAPITAN = "CAPITAN", "Capitán"
    DELEGADO = "DELEGADO", "Delegado"


class TipoActivacionCapacidad(models.TextChoices):
    """Origen de una activación de capacidad.

    `INICIAL` es la del ALTA de la inscripción; `EXPANSION` es la de una
    COMPRA DE CUPO EXTRA. La diferencia importa para los beneficios
    `FIJO_INICIAL`: una ampliación NO los vuelve a conceder (`RN-I06`).
    """

    INICIAL = "INICIAL", "Inicial"
    EXPANSION = "EXPANSION", "Expansión"


class CausaOperativaPool(models.TextChoices):
    """Causa operativa de una operación sobre el pool.

    La declara el dominio y la publica el presenter (`RN-A02`): el
    controller no decide causas.
    """

    PARTICIPACION_AGREGADA = "PARTICIPACION_AGREGADA", "Participante agregado"
    PARTICIPACION_RETIRADA = "PARTICIPACION_RETIRADA", "Participante retirado"
    CUPO_REASIGNADO = "CUPO_REASIGNADO", "Cupo reasignado"


class CausaOperativaCompraCupos(models.TextChoices):
    """Causa operativa de la compra de cupos extra."""

    COMPRA_CUPOS_CREADA = "COMPRA_CUPOS_CREADA", "Compra de cupos creada"
    COMPRA_CUPOS_REUTILIZADA = "COMPRA_CUPOS_REUTILIZADA", "Compra de cupos pendiente"


#: Tipo de concepto de línea de compra que representa el ALTA de un paquete.
CONCEPTO_LINEA_PAQUETE = "PAQUETE"

#: Tipo de concepto de línea de compra que representa una AMPLIACIÓN de cupos.
CONCEPTO_LINEA_CUPO = "CUPO"

#: Mínimo de cupos que se pueden comprar en una ampliación (`FL-04` paso 2).
MIN_CUPOS_POR_AMPLIACION = 1

#: Máximo de cupos que se pueden comprar en una ampliación (`FL-04` paso 2:
#: "se valida límite"). Es un LÍMITE DE DOMINIO declarado, no un dato del
#: cliente: la ampliación se rechaza con `CUPO_INVALIDO` si lo supera.
#:
#: PENDIENTE DE CONFIRMAR por producto (A0): el número exacto del tope no está
#: congelado por ningún contrato; se declara un valor conservador y explícito
#: para que el límite EXISTA (la regla lo exige) sin inventar una política
#: de inventario.
MAX_CUPOS_POR_AMPLIACION = 50

#: Longitud máxima de la referencia de una inscripción.
MAX_LEN_REFERENCIA_INSCRIPCION = 120

#: Mínimo de equipos que una inscripción debe declarar para poder comprar.
MIN_EQUIPOS_POR_INSCRIPCION = 1

#: Máximo de equipos que una inscripción puede declarar en el alta.
MAX_EQUIPOS_POR_INSCRIPCION = 20

# ── Códigos de máquina del activador de derechos (DOM-02) ───────────────────
#
# Los publica el coordinador de `commerce` como `error.code` de la
# incidencia y como `detalle.codigo`. Deben cumplir `^[A-Z0-9_]{1,64}$`.

#: La capacidad se habilitó.
CODIGO_CAPACIDAD_ACTIVADA = "CAPACIDAD_ACTIVADA"

#: La capacidad ya estaba habilitada: la activación es idempotente.
CODIGO_CAPACIDAD_YA_ACTIVADA = "CAPACIDAD_YA_ACTIVADA"

#: La compra no pertenece a este módulo: su referencia no es conocida.
CODIGO_REFERENCIA_NO_RECONOCIDA = "REFERENCIA_NO_RECONOCIDA"

#: La inscripción de la referencia no existe.
CODIGO_INSCRIPCION_NO_ENCONTRADA = "INSCRIPCION_NO_ENCONTRADA"

#: El snapshot de la compra no habilita ningún cupo.
CODIGO_SIN_CUPOS_ACTIVABLES = "SIN_CUPOS_ACTIVABLES"


__all__ = [
    "CONCEPTO_LINEA_CUPO",
    "CONCEPTO_LINEA_PAQUETE",
    "CODIGO_CAPACIDAD_ACTIVADA",
    "CODIGO_CAPACIDAD_YA_ACTIVADA",
    "CODIGO_INSCRIPCION_NO_ENCONTRADA",
    "CODIGO_REFERENCIA_NO_RECONOCIDA",
    "CODIGO_SIN_CUPOS_ACTIVABLES",
    "MAX_CUPOS_POR_AMPLIACION",
    "MAX_EQUIPOS_POR_INSCRIPCION",
    "MAX_LEN_REFERENCIA_INSCRIPCION",
    "MIN_CUPOS_POR_AMPLIACION",
    "MIN_EQUIPOS_POR_INSCRIPCION",
    "CausaOperativaCompraCupos",
    "CausaOperativaInscripcion",
    "CausaOperativaPool",
    "EstadoDisciplina",
    "EstadoEquipo",
    "EstadoInscripcion",
    "EstadoPaquete",
    "EstadoParticipacion",
    "ModalidadDisciplina",
    "RolParticipante",
    "TipoActivacionCapacidad",
    "TipoBeneficioPaquete",
]
