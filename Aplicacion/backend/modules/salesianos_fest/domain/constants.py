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

Packet `DOM-03` añade:

12. `EstadoPase` — `VIGENTE` / `RETIRADO`. Un pase `RETIRADO` no se ofrece
    ni se compra: el catálogo histórico se conserva.
13. `EstadoCompraPase` — `PENDIENTE` / `PAGADA` / `ANULADA`. Es el hecho
    COMERCIAL de la compra de pases: una compra `PENDIENTE` NO habilita
    ningún derecho (`RN-P02`).
14. `OrigenDerechoPase` — `COMPRA` / `CORTESIA`. Discrimina el ORIGEN de un
    derecho de entrada. Los dos orígenes convergent en la MISMA tabla de
    derechos, y por eso la no duplicación es UNA sola regla (`RN-P02`).
15. `EstadoDerechoPase` — `ACTIVO` / `REVOCADO`. La revocación es
    PERMANENTE (`RN-P08`).
16. `EstadoCortesiaPase` — `ACTIVA` / `REVOCADA`.
17. `CausaOperativaCompraPase` — la causa operativa que el presenter publica
    de la compra de pases (`RN-A02`).

Este archivo NO declara precios, ni reglas de elegibilidad, ni la regla de
reparto de beneficios `POR_CUPO` (sigue ABIERTA: `PD-09`), ni la
titularidad del beneficio grupal `BOX` (sigue ABIERTA: `PD-01`).
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


class EstadoPase(models.TextChoices):
    """Estado comercial de un pase dentro de su edición.

    `VIGENTE` es el único estado que se ofrece y se compra. `RETIRADO`
    conserva el catálogo histórico sin permitir una compra nueva.
    """

    VIGENTE = "VIGENTE", "Vigente"
    RETIRADO = "RETIRADO", "Retirado"


class EstadoCompraPase(models.TextChoices):
    """Estado comercial de la COMPRA de un lote de pases.

    `PENDIENTE` es el estado en el que queda la compra recién creada: **no
    habilita ningún derecho**. Los pases sólo se pueden asignar cuando la
    compra está `PAGADA`, que es lo que hace la ACTIVACIÓN de derechos de
    `FND-05` (`RN-P02`, `QA-P01`).
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA = "PAGADA", "Pagada"
    ANULADA = "ANULADA", "Anulada"


class OrigenDerechoPase(models.TextChoices):
    """ORIGEN de un derecho de entrada (`RN-P02`).

    - `COMPRA` — el derecho lo financia una compra pagada.
    - `CORTESIA` — el derecho lo otorga un administrador, con motivo y
      auditoría, y **sin** compra, orden ni transacción (`RN-P05`).

    Los dos orígenes se materializan en la MISMA tabla de derechos: así la
    regla de no duplicación es UNA sola, y un derecho comprado no puede
    coexistir con una cortesía del mismo tipo para la misma persona.
    """

    COMPRA = "COMPRA", "Compra"
    CORTESIA = "CORTESIA", "Cortesía"


class EstadoDerechoPase(models.TextChoices):
    """Estado de un derecho de entrada.

    `REVOCADO` es TERMINAL para validaciones futuras: los consumos ya
    occurring quedan en el historial (`RN-P08`).
    """

    ACTIVO = "ACTIVO", "Activo"
    REVOCADO = "REVOCADO", "Revocado"


class EstadoCortesiaPase(models.TextChoices):
    """Estado del ACTA de una cortesía.

    `REVOCADA` deja el historial: la cortesía existió y se anuló, con actor
    y motivo (`RN-P05`, `FL-07` paso 4).
    """

    ACTIVA = "ACTIVA", "Activa"
    REVOCADA = "REVOCADA", "Revocada"


class CausaOperativaCompraPase(models.TextChoices):
    """Causa operativa de la compra de pases.

    Es la diferencia entre "la acabo de crear" y "ya existía y la reutilicé".
    La publica el PRESENTER: el controller no decide causas (`RN-A02`).
    """

    COMPRA_PASE_CREADA = "COMPRA_PASE_CREADA", "Compra de pases creada"
    COMPRA_PASE_REUTILIZADA = "COMPRA_PASE_REUTILIZADA", "Compra de pases pendiente"


#: Tipo de concepto de línea de compra que representa una COMPRA DE PASES.
CONCEPTO_LINEA_PASE = "PASE"

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

# ── Códigos de máquina del activador de derechos de PASES (DOM-03) ───────────
#
# Mismo contrato que los de `DOM-02`: los publica el coordinador de
# `commerce` como `error.code` de la incidencia y como `detalle.codigo`.
# Deben cumplir `^[A-Z0-9_]{1,64}$`.

#: Los pases de la compra quedaron habilitados.
CODIGO_PASES_ACTIVADOS = "PASES_ACTIVADOS"

#: Los pases ya estaban habilitados: la activación es idempotente.
CODIGO_PASES_YA_ACTIVADOS = "PASES_YA_ACTIVADOS"

#: La compra de pases de la referencia no existe.
CODIGO_COMPRA_PASE_NO_ENCONTRADA = "COMPRA_PASE_NO_ENCONTRADA"

#: La referencia de la compra no es de este módulo.
CODIGO_REFERENCIA_PASE_NO_RECONOCIDA = "REFERENCIA_PASE_NO_RECONOCIDA"

#: El snapshot de la compra no habilita ningún pase.
CODIGO_SIN_PASES_ACTIVABLES = "SIN_PASES_ACTIVABLES"

# ── Límites y credenciales de los pases (DOM-03) ────────────────────────────

#: Mínimo de pases que se pueden comprar en una sola operación.
MIN_PASES_POR_COMPRA = 1

#: Máximo de pases que se pueden comprar en una sola operación.
#:
#: Es un LÍMITE DE DOMINIO declarado, no un dato del cliente: la compra se
#: rechaza con `CANTIDAD_INVALIDA` si lo supera.
#:
#: PENDIENTE DE CONFIRMAR por producto (A0): el número exacto del tope no está
#: congelado por ningún contrato; se declara un valor conservador y explícito
#: para que el límite EXISTA sin inventar una política de inventario.
MAX_PASES_POR_COMPRA = 50

#: Moneda por defecto del catálogo de pases (ISO-4217).
MONEDA_PASE = "PEN"

#: Longitud máxima del token privado de gestión de una compra de pases.
MAX_LEN_TOKEN_PASE = 64

#: Longitud máxima de la referencia de intención de una compra de pases.
MAX_LEN_REFERENCIA_PASE = 200

#: Vigencia por defecto del token privado de gestión, en días.
#:
#: PENDIENTE DE CONFIRMAR por producto (A0): `GOV-01-OPEN-05` deja ABIERTA la
#: política exacta de expiración, rotación de enlaces y verificación de
#: contacto. El MECANISMO está congelado (vencimiento, ámbito por compra y
#: revocabilidad); el número concreto se declara conservador y explícito
#: para que el vencimiento EXISTA sin inventar una política de negocio.
VIGENCIA_TOKEN_PASE_DIAS = 30

#: Cabecera HTTP por la que viaja el token privado de gestión de la compra.
#:
#: Es una CREDENCIAL: nunca viaja en la query string (queda en los logs del
#: servidor y del proxy) y nunca se publica en un listado.
CABECERA_TOKEN_PASE = "X-Pase-Token"

#: Longitud mínima del motivo de una cortesía (`RN-P05`).
MIN_LEN_MOTIVO_CORTESIA = 5

#: Longitud máxima del motivo de una cortesía.
MAX_LEN_MOTIVO_CORTESIA = 500


__all__ = [
    "CABECERA_TOKEN_PASE",
    "CONCEPTO_LINEA_CUPO",
    "CONCEPTO_LINEA_PAQUETE",
    "CONCEPTO_LINEA_PASE",
    "CODIGO_CAPACIDAD_ACTIVADA",
    "CODIGO_CAPACIDAD_YA_ACTIVADA",
    "CODIGO_COMPRA_PASE_NO_ENCONTRADA",
    "CODIGO_INSCRIPCION_NO_ENCONTRADA",
    "CODIGO_PASES_ACTIVADOS",
    "CODIGO_PASES_YA_ACTIVADOS",
    "CODIGO_REFERENCIA_NO_RECONOCIDA",
    "CODIGO_REFERENCIA_PASE_NO_RECONOCIDA",
    "CODIGO_SIN_CUPOS_ACTIVABLES",
    "CODIGO_SIN_PASES_ACTIVABLES",
    "MAX_CUPOS_POR_AMPLIACION",
    "MAX_EQUIPOS_POR_INSCRIPCION",
    "MAX_LEN_MOTIVO_CORTESIA",
    "MAX_LEN_REFERENCIA_INSCRIPCION",
    "MAX_LEN_REFERENCIA_PASE",
    "MAX_LEN_TOKEN_PASE",
    "MAX_PASES_POR_COMPRA",
    "MIN_CUPOS_POR_AMPLIACION",
    "MIN_EQUIPOS_POR_INSCRIPCION",
    "MIN_LEN_MOTIVO_CORTESIA",
    "MIN_PASES_POR_COMPRA",
    "MONEDA_PASE",
    "VIGENCIA_TOKEN_PASE_DIAS",
    "CausaOperativaCompraCupos",
    "CausaOperativaCompraPase",
    "CausaOperativaInscripcion",
    "CausaOperativaPool",
    "EstadoCompraPase",
    "EstadoCortesiaPase",
    "EstadoDerechoPase",
    "EstadoDisciplina",
    "EstadoEquipo",
    "EstadoInscripcion",
    "EstadoPaquete",
    "EstadoParticipacion",
    "EstadoPase",
    "ModalidadDisciplina",
    "OrigenDerechoPase",
    "RolParticipante",
    "TipoActivacionCapacidad",
    "TipoBeneficioPaquete",
]
