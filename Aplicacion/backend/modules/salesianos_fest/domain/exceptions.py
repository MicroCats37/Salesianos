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
from ninja.errors import HttpError


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


# ── DOM-03 · PASES, BENEFICIARIOS Y CORTESÍA ───────────────────────────────
#
# `PASE_NO_DISPONIBLE` (409) y `CANTIDAD_INVALIDA` (422) están CONGELADOS
# por el ledger `FR-07` §3.3 para `RT-CM-02`; `PASE_NO_TRANSFERIBLE` (409) y
# `PASE_BENEFICIARIO_NO_ENCONTRADO` (404) lo están para `RT-RT-03`. El resto
# son códigos PROPUESTOS y A0 debe añadirlos al catálogo público con su
# prosa.


class PaseNoDisponibleError(ConflictError):
    """El pase no se puede comprar (409).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-02` (409).
    Cubre los TRES casos del mismo hecho comercial:

    1. El pase no existe en la edición pedida.
    2. El pase está `RETIRADO`.
    3. El pase no tiene un PRECIO VIGENTE.

    El tercer caso es la regla "no inventar un precio de reserva": un pase
    sin precio vigente NO tiene precio de invención, no se ofrece y no se
    compra.
    """

    code = "PASE_NO_DISPONIBLE"

    def __init__(self):
        super().__init__(
            "El pase seleccionado no está disponible para esta edición.",
            code=self.code,
        )


class CantidadInvalidaError(UnprocessableEntityError):
    """La cantidad de pases solicitados no es válida (422).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-02` (422).
    Cubre la cantidad fuera de los límites de dominio.
    """

    code = "CANTIDAD_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La cantidad de pases solicitados no es válida.",
            code=self.code,
        )


class PaseNoEncontradoError(NotFoundError):
    """El pase solicitado no existe o no pertenece a la edición (404).

    Código REQUESTED a A0.
    """

    code = "PASE_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Pase", code=self.code)


class CompraPaseNoEncontradaError(NotFoundError):
    """La compra de pases solicitada no existe (404).

    Es el mismo hecho que un recurso ausente: la respuesta NO revela si
    existe una compra de OTRO actor (`FR-03` §2.1 regla 4).

    Código REQUESTED a A0.
    """

    code = "COMPRA_PASE_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Compra de pases", code=self.code)


class PaseBeneficiarioNoEncontradoError(NotFoundError):
    """El beneficiario solicitado no existe en la compra (404).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-RT-03` (404).
    """

    code = "PASE_BENEFICIARIO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Beneficiario de pase", code=self.code)


class PaseNoTransferibleError(ConflictError):
    """El derecho ya no se puede transferir (409).

    CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-RT-03` (409).

    Cubre los casos en que la operación NO puede ejecutarse sobre el
    derecho: el derecho ya está revocado (`RN-P08`) o la compra no está
    pagada (`RN-P02`).

    La LIBERACIÓN del cupo y el REEMPLAZO del titular tras una revocación
    siguen ABIERTOS (`PD-02` / `GOV-01-OPEN-08`): este paquete congela la
    INTERFAZ de la revocación, no la política comercial.

    Código REQUESTED a A0.
    """

    code = "PASE_NO_TRANSFERIBLE"

    def __init__(self):
        super().__init__(
            "El pase no se puede transferir en su estado actual.",
            code=self.code,
        )


class PaseDuplicadoError(ConflictError):
    """La persona ya tiene un derecho activo de ese pase (409).

    La garantía de NO duplicar el derecho es de la base de datos (restricción
    única parcial `(edicion, pase, persona) WHERE estado = 'ACTIVO'`); esta
    excepción es la traducción legible de esa restricción.

    Vale para los DOS orígenes: una cortesía no puede duplicar una compra,
    ni al revés (`RN-P02`, `RN-P07`).

    Código REQUESTED a A0.
    """

    code = "PASE_DUPLICADO"

    def __init__(self):
        super().__init__(
            "La persona ya tiene un pase activo de este tipo en la edición.",
            code=self.code,
        )


class SinPasesDisponiblesError(ConflictError):
    """La compra no tiene pases libres para asignar (409).

    El saldo lo calcula el servidor: sólo se puede asignar la capacidad
    PAGADA (`RN-P02`). No es un saldo negativo: es la ausencia de capacidad.

    Código REQUESTED a A0.
    """

    code = "SIN_PASES_DISPONIBLES"

    def __init__(self):
        super().__init__(
            "No hay pases disponibles para asignar en esta compra.",
            code=self.code,
        )


class CompraPaseNoPagadaError(ConflictError):
    """La compra todavía no está pagada (409).

    Una compra `PENDIENTE` NO habilita ningún derecho (`RN-P02`, `QA-P01`).
    Los pases se pueden asignar sólo después de que la ACTIVACIÓN de
    derechos los habilite.

    Código REQUESTED a A0.
    """

    code = "COMPRA_PASE_NO_PAGADA"

    def __init__(self):
        super().__init__(
            "La compra de pases todavía no está pagada.",
            code=self.code,
        )


class TokenPaseInvalidoError(HttpError):
    """El enlace de gestión no es válido (401).

    Es un fallo de AUTENTICACIÓN, no de autorización: el token ES la
    credencial del enlace privado (`contratos/02` §5). Por eso el status es
    **401** y no 403 — la autoridad de permisos responde 401 antes que 403.

    El token ausente, expirado o revocado es el mismo caso: no se puede
    distinguir por el mismo canal, y el mensaje público es genérico.

    Código REQUESTED a A0.
    """

    code = "TOKEN_PASE_INVALIDO"

    def __init__(self):
        super().__init__(401, "El enlace de gestión del pase no es válido.")


class ActorRequeridoError(HttpError):
    """La operación exige una cuenta autenticada (401).

    Es la defensa en profundidad de las rutas que ya declaran
    `IsAuthenticated`: si la petición llegara sin cuenta, el dominio la
    rechaza con un código estable en lugar de operar sin ACTOR.

    Una cortesía SIN actor no es auditable (`RN-P05`).

    Código REQUESTED a A0.
    """

    code = "ACTOR_REQUERIDO"

    def __init__(self):
        super().__init__(401, "Debes iniciar sesión para realizar esta operación.")


class CompraPaseNoAutorizadaError(ForbiddenError):
    """El actor no es el titular de la compra (403).

    La titularidad la decide el MÓDULO DUEÑO del recurso (`FR-03` §2.1):
    ser `Administrador` NO sustituye la titularidad de una compra ajena.
    El token es de ÁMBITO POR COMPRA: el token de otra compra no abre esta.

    Código REQUESTED a A0.
    """

    code = "COMPRA_PASE_NO_AUTORIZADA"

    def __init__(self):
        super().__init__(
            "No tiene autorización para gestionar esta compra de pases.",
        )


class CortesiaMotivoInvalidoError(UnprocessableEntityError):
    """La cortesía no tiene un motivo válido (422).

    El motivo es OBLIGATORIO (`RN-P05`): una cortesía sin motivo no es
    auditable y no se registra.

    Código REQUESTED a A0.
    """

    code = "CORTESIA_MOTIVO_INVALIDO"

    def __init__(self):
        super().__init__(
            message="El motivo de la cortesía es obligatorio.",
            code=self.code,
        )


class CortesiaNoEncontradaError(NotFoundError):
    """La cortesía solicitada no existe (404).

    Código REQUESTED a A0.
    """

    code = "CORTESIA_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Cortesía", code=self.code)


# ── PROMOCIONES, CATEGORÍAS Y COTIZACIÓN (restore-registration-promotion-…) ──
#
# `PROMOCION_NO_ENCONTRADA` (404), `CATEGORIA_NO_RESUELTA` (422),
# `FUSION_PROMOCION_INVALIDA` (422) y `CANTIDAD_INVALIDA` (422) son códigos
# PROPUESTOS: A0 debe añadirlos al catálogo público con su prosa. `CANTIDAD_INVALIDA`
# ya existe en el catálogo (lo declaró `DOM-03` para los pases) y se REUSA: es
# el mismo hecho — "la cantidad pedida no es válida" — en otro flujo.


class PromocionNoEncontradaError(NotFoundError):
    """La promoción indicada no existe o no está activa (404).

    La promoción es GLOBAL: no cuelga de ninguna edición. La compara el
    servidor contra el catálogo; el cliente no puede declarar una promoción
    que no existe.

    Código REQUESTED a A0.
    """

    code = "PROMOCION_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Promoción", code=self.code)


class CategoriaNoResueltaError(UnprocessableEntityError):
    """La promoción de la inscripción no cae en ninguna categoría (422).

    Es la DERIVACIÓN server-side de la banda competitiva: la promoción
    principal se proyecta contra el rango `[promocion_desde, promocion_hasta]`
    de las categorías ACTIVAS de la edición. Si ninguna categoría contiene el
    año de la cohorte, la inscripción NO tiene banda con la que competir: se
    rechaza en vez de inventar una.

    Código REQUESTED a A0.
    """

    code = "CATEGORIA_NO_RESUELTA"

    def __init__(self):
        super().__init__(
            message=(
                "La promoción seleccionada no corresponde a ninguna categoría "
                "de esta edición."
            ),
            code=self.code,
        )


class FusionPromocionInvalidaError(UnprocessableEntityError):
    """La promoción fusionada no es válida (422).

    Cubre el único caso que el servidor puede rechazar por sí mismo: la
    promoción fusionada es la MISMA que la principal. Una fusión no es un
    alias de la promoción principal: no aporta información.

    La fusión es DESCRIPTIVA (`D-CAT-02`): no altera cupos, pago, categoría,
    elegibilidad de equipo ni cuadro competitivo.

    Código REQUESTED a A0.
    """

    code = "FUSION_PROMOCION_INVALIDA"

    def __init__(self):
        super().__init__(
            message=(
                "La promoción fusionada debe ser distinta de la promoción "
                "principal."
            ),
            code=self.code,
        )


class CantidadInsuficienteError(UnprocessableEntityError):
    """La cantidad de participantes no alcanza el mínimo del paquete (422).

    El mínimo COMERCIAL es del paquete (`Paquete.minimo_compra_inicial`): el
    cliente declara cuántos participantes inscriben, y el servidor exige que
    la cantidad sea válida contra ese mínimo.

    No hay un máximo global de participantes: el tope de un equipo es el de
    su disciplina (`Disciplina.maximo_por_equipo`), que es una regla
    deportiva, no comercial.

    Código REQUESTED a A0. Es un código PROPIO y no reutiliza el
    `CANTIDAD_INVALIDA` de los pases: ese código ya tiene una prosa pública
    que habla de PASES, y reutilizarlo publicaría una frase falsa.
    """

    code = "CANTIDAD_INSUFICIENTE"

    def __init__(self):
        super().__init__(
            message=(
                "La cantidad de participantes no alcanza el mínimo de compra "
                "del paquete."
            ),
            code=self.code,
        )


class PrecioCambiadoError(ConflictError):
    """El precio del catálogo se movió entre la cotización y el alta (409).

    Es la regla de CONCURRENCIA de la cotización: el cliente devuelve el
    token `cotizacion_version` que recibió y, si el catálogo ya no está en
    la versión que se cotizó, el alta se rechaza en vez de cobrar una
    cantidad sin que el comprador la haya visto.

    Sin token (alta sin cotización previa) NO hay comprobación: el precio
    vigente es el que rige (`RN-C02`).

    Código REQUESTED a A0.
    """

    code = "PRECIO_CAMBIADO"

    def __init__(self):
        super().__init__(
            "El precio del paquete cambió desde la cotización. Vuelve a cotizar.",
            code=self.code,
        )


class EquiposFueraDePaqueteError(UnprocessableEntityError):
    """Los equipos declarados no cumplen la regla de disciplinas (422).

    El servidor, no el cliente, decide cuántos equipos puede declarar una
    inscripción con un paquete concreto:

    - `modo_disciplinas = FIJO` — hay que declarar EXACTAMENTE las
      disciplinas vinculadas al paquete.
    - `modo_disciplinas = ELEGIBLE` — hay que declarar hasta
      `cantidad_disciplinas` de las disciplinas vinculadas al paquete.

    El cliente no puede declarar equipos de más ni de menos.

    Código REQUESTED a A0.
    """

    code = "EQUIPOS_FUERA_DE_PAQUETE"

    def __init__(self):
        super().__init__(
            message=(
                "Los equipos declarados no corresponden a las disciplinas "
                "permitidas por el paquete."
            ),
            code=self.code,
        )


__all__ = [
    "ActorRequeridoError",
    "CantidadInsuficienteError",
    "CantidadInvalidaError",
    "CategoriaNoResueltaError",
    "CompraNoAutorizadaError",
    "CompraPaseNoAutorizadaError",
    "CompraPaseNoEncontradaError",
    "CompraPaseNoPagadaError",
    "CompradorSinPersonaError",
    "CortesiaMotivoInvalidoError",
    "CortesiaNoEncontradaError",
    "CupoInvalidoError",
    "DisciplinaNoPermitidaError",
    "EquipoCompletoError",
    "EquipoDuplicadoError",
    "EquipoNoEncontradoError",
    "EquiposFueraDePaqueteError",
    "FusionPromocionInvalidaError",
    "InscripcionNoAutorizadaError",
    "InscripcionNoEncontradaError",
    "PaqueteNoVigenteError",
    "PaseBeneficiarioNoEncontradoError",
    "PaseDuplicadoError",
    "PaseNoDisponibleError",
    "PaseNoEncontradoError",
    "PaseNoTransferibleError",
    "ParticipanteDuplicadoError",
    "ParticipanteNoElegibleError",
    "ParticipanteNoEncontradoError",
    "PersonaNoEncontradaError",
    "PrecioCambiadoError",
    "PromocionNoEncontradaError",
    "SinCuposDisponiblesError",
    "SinPasesDisponiblesError",
    "TokenPaseInvalidoError",
]
