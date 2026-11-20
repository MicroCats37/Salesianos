"""
Excepciones de dominio del módulo `usuarios`.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3.

Reglas que se aplican a TODAS estas excepciones
(`contract/django-app-architecture-contract.md` §10,
`contract/api-wrapper-presenter-contract.md` §8):

- Declaran un `code` estable y legible por máquina.
- El TEXTO que construyen es técnico: nunca sale al cliente.
- El mensaje público lo decide el catálogo `core/exceptions.py` a partir del
  `code`. Un código que todavía no está catalogado devuelve la prosa genérica
  del status HTTP, nunca el texto crudo de la excepción.
- No interpolan UUIDs, ids internos, SQL ni payloads de proveedores.

Los códigos `PERSONA_NO_ENCONTRADA` y `TIPO_DOCUMENTO_INVALIDO` ya están en el
catálogo público. `FUENTE_EXTERNA_NO_DISPONIBLE`, `FUENTE_EXTERNA_TIMEOUT` y
`PERSONA_DUPLICADA` provenían del ledger `RT-ID-02`/`RT-ID-03` (`FR-07`) y su
prosa pública está REQUESTED a A0 (ver la evidencia del paquete FND-03).

`AUTH_ERROR` (credenciales inválidas) ya está en el catálogo público.
`CUENTA_INACTIVA` es un código NUEVO de este módulo: su prosa pública está
REQUESTED a A0 (evidencia del paquete FND-03A).
"""

from core.exceptions import ConflictError, NotFoundError, UnprocessableEntityError
from ninja.errors import HttpError


class CredencialesInvalidasError(HttpError):
    """Las credenciales no son válidas (401).

    Es la RESPUESTA NEUTRA del inicio de sesión: el MISMO código, el mismo
    status y la misma prosa pública tanto si el identificador no existe como
    si la contraseña no cuadra. La respuesta NO distingue un caso del otro,
    así que no filtra qué cuentas existen (`FR-01` §4.4 — categoría
    "Authentication"; `RN-U04`).

    El código `AUTH_ERROR` ya está en el catálogo público de
    `core/exceptions.py`, así que la prosa que ve el usuario sale de ahí y
    nunca del texto técnico de esta excepción.
    """

    code = "AUTH_ERROR"

    def __init__(self):
        super().__init__(401, "Credenciales inválidas.")


class CuentaInactivaError(HttpError):
    """La cuenta está desactivada (403).

    Es un estado DISTINTO de "credenciales inválidas": la contraseña es
    correcta, pero la cuenta no puede operar. Django impide que una cuenta
    inactiva se autentique, así que el módulo lo discrimina antes de
    responder.

    El código `CUENTA_INACTIVA` viaja estable en `error.code`; la prosa
    pública la decide el catálogo de `core/exceptions.py` (A0) y, hasta que
    lo catalogue, cae a la prosa genérica del status 403 — nunca al texto
    crudo de esta excepción (`FR-01` §4.4).
    """

    code = "CUENTA_INACTIVA"

    def __init__(self):
        super().__init__(403, "La cuenta está desactivada.")


class PersonaNoEncontradaError(NotFoundError):
    """No hay una `Persona` registrada con ese documento (404).

    El mensaje NO confirma ni desmiente cuentas, contactos ni credenciales:
    sólo dice que no existe una persona con ese documento.
    """

    code = "PERSONA_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Persona", code=self.code)


class TipoDocumentoInvalidoError(UnprocessableEntityError):
    """El tipo de documento está fuera del vocabulario cerrado (422)."""

    code = "TIPO_DOCUMENTO_INVALIDO"

    def __init__(self):
        super().__init__(
            message="El tipo de documento no es válido.",
            code=self.code,
        )


class PersonaDatosIncompletosError(UnprocessableEntityError):
    """La fuente externa respondió sin datos utilizables (422).

    Es un estado DISTINTO de "no encontrado" y de "fuente no disponible"
    (`FR-03` §3.3): el documento existe, pero la respuesta no permite construir
    una identidad. Prohibido fabricar los datos que faltan.
    """

    code = "PERSONA_DATOS_INCOMPLETOS"

    def __init__(self):
        super().__init__(
            message="La fuente externa no devolvió datos suficientes.",
            code=self.code,
        )


class PersonaDuplicadaError(ConflictError):
    """El documento ya está vinculado a una cuenta (409).

    La `Persona` existe y su cuenta ya está creada: la identidad no se vuelve
    a crear ni se reescribe (`FR-03` §1.2 — el nacimiento de cuenta es una
    operación explícita, nunca un efecto lateral de resolver un documento).
    """

    code = "PERSONA_DUPLICADA"

    def __init__(self):
        super().__init__(
            message="Ese documento ya está vinculado a una cuenta.",
            code=self.code,
        )


class EmailYaRegistradoError(ConflictError):
    """El correo electrónico ya está vinculado a una cuenta (409).

    El email es la clave ÚNICA y NO NULA de la cuenta
    (`unique_email_usuario_no_vacio`): dos cuentas no pueden compartirlo.

    El código `CONFLICT` es el del catálogo público de `core/exceptions.py`:
    mientras A0 no catalogue un código propio para este caso
    (`EMAIL_YA_REGISTRADO`), la prosa pública es la genérica del 409 — nunca
    el texto técnico de esta excepción (`FR-01` §4.4).
    """

    code = "CONFLICT"

    def __init__(self):
        super().__init__(
            message="El correo electrónico ya está registrado.",
            code=self.code,
        )


class FuenteExternaNoDisponibleError(HttpError):
    """La fuente externa de documentos falló o no está configurada (503).

    Es RECUPERABLE: el cliente puede reintentar. Nunca se fabrica una
    identidad para "salvar" la operación (`contratos/03` §7).
    """

    code = "FUENTE_EXTERNA_NO_DISPONIBLE"

    def __init__(self):
        super().__init__(503, "La fuente externa de documentos no está disponible.")


class FuenteExternaTimeoutError(HttpError):
    """La fuente externa de documentos agotó el tiempo de espera (504).

    Es RECUPERABLE y DISTINTO de "fuente no disponible" (`FR-03` §3.3).
    """

    code = "FUENTE_EXTERNA_TIMEOUT"

    def __init__(self):
        super().__init__(504, "La fuente externa de documentos no respondió a tiempo.")


__all__ = [
    "CredencialesInvalidasError",
    "CuentaInactivaError",
    "EmailYaRegistradoError",
    "FuenteExternaNoDisponibleError",
    "FuenteExternaTimeoutError",
    "PersonaDatosIncompletosError",
    "PersonaDuplicadaError",
    "PersonaNoEncontradaError",
    "TipoDocumentoInvalidoError",
]
