"""Excepciones de dominio del módulo `salesianos_fest`.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Reglas que se aplican a TODAS estas excepciones
(`contract/django-app-architecture-contract.md` §10,
`contract/api-wrapper-presenter-contract.md` §8):

- Declaran un `code` estable y legible por máquina.
- El TEXTO que construyen es técnico: **nunca** sale al cliente.
- El mensaje público lo decide el catálogo `core/exceptions.py` a partir del
  `code`. Los códigos marcados como REQUESTED abajo necesitan que A0 los
  añada al catálogo (este paquete NO edita `core/exceptions.py`).

Códigos ya catalogados por A0: `EDICION_NO_ENCONTRADA`, `EDICION_NO_PUBLICADA`,
`MODULO_NO_HABILITADO`, `COMPRA_NO_AUTORIZADA`, `ACTION_NOT_ALLOWED`.

Packet `DOM-02` añade las excepciones del POOL y de la AMPLIACIÓN. Los
códigos `COMPRA_NO_AUTORIZADA` (403) y `CUPO_INVALIDO` (422) están CONGELADOS
por el ledger `FR-07` §3.3 para `RT-CM-01`; el resto son códigos PROPUESTOS
y A0 debe añadirlos al catálogo público con su prosa.

Un código que todavía no está en el catálogo NO rompe la respuesta: el
catálogo cae al mensaje genérico del status HTTP (`core/exceptions.py` §1).
"""

from core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)


class PaqueteNoVigenteError(ConflictError):
    """El paquete no se puede comprar (409).

    Cubre los TRES casos de negocio del mismo hecho comercial:

    1. El paquete no existe en la edición pedida.
    2. El paquete está `RETIRADO`.
    3. El paquete no tiene un PRECIO VIGENTE.

    El tercer caso es la regla "no inventar un precio de reserva"
    (`FL-01` paso 3): un paquete sin precio vigente NO tiene precio de
    invención, no se ofrece y no se compra.

    Código REQUESTED a A0 (ya declarado por el ledger `FR-07` §3.3 para
    `RT-CM-01` → 409).
    """

    code = "PAQUETE_NO_VIGENTE"

    def __init__(self):
        super().__init__(
            "El paquete seleccionado no está vigente para esta edición.",
            code=self.code,
        )


class DisciplinaNoPermitidaError(UnprocessableEntityError):
    """La disciplina no pertenece a la edición o al paquete (422).

    El padrón NO lo elige el cliente: el servidor exige que la disciplina
    exista en la edición, esté `ACTIVA` y esté incluida en el paquete.

    Código REQUESTED a A0.
    """

    code = "DISCIPLINA_NO_PERMITIDA"

    def __init__(self):
        super().__init__(
            message="La disciplina seleccionada no está permitida para este paquete.",
            code=self.code,
        )


class EquipoDuplicadoError(UnprocessableEntityError):
    """La inscripción declara dos equipos para la misma disciplina (422).

    Código REQUESTED a A0.
    """

    code = "EQUIPO_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="No puede declarar dos equipos para la misma disciplina.",
            code=self.code,
        )


class InscripcionNoEncontradaError(NotFoundError):
    """La inscripción solicitada no existe (404).

    Código REQUESTED a A0.
    """

    code = "INSCRIPCION_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Inscripción", code=self.code)


class InscripcionNoAutorizadaError(ForbiddenError):
    """El actor no es el responsable de la inscripción (403).

    La titularidad la decide el MÓDULO DUEÑO del recurso (`FR-03` §2.1
    regla 1) usando las primitivas puras de `usuarios.TitularidadService`:
    ser `Administrador` NO sustituye la titularidad.

    Código REQUESTED a A0.
    """

    code = "INSCRIPCION_NO_AUTORIZADA"

    def __init__(self):
        super().__init__(
            "No tiene autorización para gestionar esta inscripción.",
        )


class CompradorSinPersonaError(UnprocessableEntityError):
    """La cuenta autenticada no tiene persona vinculada (422).

    Una cuenta técnica no puede ser responsable de una inscripción: la
    inscripción tiene un responsable que es una `Persona` (`RN-I01`).

    Código REQUESTED a A0.
    """

    code = "COMPRADOR_SIN_PERSONA"

    def __init__(self):
        super().__init__(
            message="La cuenta no tiene una persona vinculada.",
            code=self.code,
        )


# ── DOM-02 · POOL, ASIGNACIÓN Y AMPLIACIÓN ───────────────────────────────────


class CompraNoAutorizadaError(ForbiddenError):
    """El actor no puede comprar cupos para esta inscripción (403).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-01`
    (`COMPRA_NO_AUTORIZADA`, 403). La titularidad la decide el MÓDULO DUEÑO
    del recurso (`FR-03` §2.1): ser `Administrador` NO sustituye la
    titularidad de una inscripción ajena.
    """

    code = "COMPRA_NO_AUTORIZADA"

    def __init__(self):
        super().__init__(
            "No tiene autorización para comprar cupos en esta inscripción.",
        )


class CupoInvalidoError(UnprocessableEntityError):
    """La cantidad de cupos de la ampliación no es válida (422).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-01`
    (`CUPO_INVALIDO`, 422). Cubre la cantidad fuera de los límites de
    dominio (`FL-04` paso 2: "se valida límite/fecha/precio").

    Código REQUESTED a A0 (aún no catalogado).
    """

    code = "CUPO_INVALIDO"

    def __init__(self):
        super().__init__(
            message="La cantidad de cupos solicitados no es válida.",
            code=self.code,
        )


class SinCuposDisponiblesError(ConflictError):
    """La inscripción no tiene cupos pagados disponibles (409).

    El saldo disponible lo calcula el servidor (`RN-I03`): cuando llega a
    cero, no se puede asignar otro cupo. No es un saldo negativo: es la
    ausencia de capacidad.

    Código REQUESTED a A0.
    """

    code = "SIN_CUPOS_DISPONIBLES"

    def __init__(self):
        super().__init__(
            "No hay cupos pagados disponibles en esta inscripción.",
            code=self.code,
        )


class ParticipanteNoElegibleError(UnprocessableEntityError):
    """La persona no cumple las reglas de elegibilidad (422).

    Cubre los rechazos que el servidor decide y el cliente NO puede
    sortear (`RN-I05`): la disciplina no está activa, no pertenece al
    paquete, no es de la edición de la inscripción, o la modalidad de la
    disciplina no es compatible con el género declarado por la persona.

    Código REQUESTED a A0.
    """

    code = "PARTICIPANTE_NO_ELEGIBLE"

    def __init__(self):
        super().__init__(
            message=(
                "La persona no cumple las condiciones de elegibilidad para "
                "este equipo."
            ),
            code=self.code,
        )


class ParticipanteDuplicadoError(UnprocessableEntityError):
    """La persona ya participa activamente en esta inscripción (422).

    La garantía de NO duplicar participación es de la base de datos
    (restricción única parcial); esta excepción es la traducción legible
    de esa restricción.

    Código REQUESTED a A0.
    """

    code = "PARTICIPANTE_DUPLICADO"

    def __init__(self):
        super().__init__(
            message="La persona ya participa activamente en esta inscripción.",
            code=self.code,
        )


class EquipoCompletoError(ConflictError):
    """El equipo alcanzó el máximo de participantes de su disciplina (409).

    Código REQUESTED a A0.
    """

    code = "EQUIPO_COMPLETO"

    def __init__(self):
        super().__init__(
            "El equipo alcanzó el máximo de participantes permitido.",
            code=self.code,
        )


class ParticipanteNoEncontradoError(NotFoundError):
    """La participación solicitada no existe o no pertenece a la inscripción (404).

    Código REQUESTED a A0.
    """

    code = "PARTICIPANTE_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Participación", code=self.code)


class EquipoNoEncontradoError(NotFoundError):
    """El equipo solicitado no existe o no pertenece a la inscripción (404).

    Código REQUESTED a A0.
    """

    code = "EQUIPO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Equipo", code=self.code)


class PersonaNoEncontradaError(NotFoundError):
    """La persona indicada no existe en el padrón (404).

    Cuando la persona se pide por documento, la resolución es de
    `usuarios` (`FR-03`): este módulo sólo consulta, no crea identidades.

    Código REQUESTED a A0.
    """

    code = "PERSONA_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Persona", code=self.code)


__all__ = [
    "CompraNoAutorizadaError",
    "CompradorSinPersonaError",
    "CupoInvalidoError",
    "DisciplinaNoPermitidaError",
    "EquipoCompletoError",
    "EquipoDuplicadoError",
    "EquipoNoEncontradoError",
    "InscripcionNoAutorizadaError",
    "InscripcionNoEncontradaError",
    "PaqueteNoVigenteError",
    "ParticipanteDuplicadoError",
    "ParticipanteNoElegibleError",
    "ParticipanteNoEncontradoError",
    "PersonaNoEncontradaError",
    "SinCuposDisponiblesError",
]
