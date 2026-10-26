"""
Domain exceptions for the administracion module.

Every exception carries a STABLE machine-readable `code`. The public message
the user sees always comes from the catalog `core/exceptions.py::PUBLIC_ERROR_MESSAGES`
— never from the exception itself
(`contract/api-wrapper-presenter-contract.md` §8).
"""

from core.exceptions import NotFoundError, UnprocessableEntityError


class EventoActivoNoEncontradoError(NotFoundError):
    """No hay ningún evento activo configurado (404).

    El área de administración SIEMPRE opera sobre el evento activo, resuelto
    en el servidor a partir de `settings.EVENTO_ACTIVO_NOMBRE`. Cuando no
    existe ninguna edición activa, el endpoint no puede inventar un alcance:
    responde 404 con el código estable `EVENTO_ACTIVO_NO_ENCONTRADO`.

    El mensaje público sale del catálogo `core/exceptions.py::PUBLIC_ERROR_MESSAGES`;
    esta excepción no interpola identificadores internos.
    """

    code: str = "EVENTO_ACTIVO_NO_ENCONTRADO"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Evento activo", code=self.code)


class InvalidOrderingError(UnprocessableEntityError):
    """El criterio de ordenamiento solicitado no está en la lista blanca.

    El ordenamiento es SIEMPRE una lista blanca del servidor: el cliente pide
    un nombre de campo público (`created_at`, `estado`, ...) y el backend lo
    traduce a la expresión ORM autorizada. Un valor desconocido se rechaza con
    422 `INVALID_REQUEST`; NUNCA se inyecta el texto del cliente en el
    queryset.

    El mensaje público sale del catálogo; esta excepción no interpola el valor
    recibido (podría contener basura del cliente).
    """

    code: str = "INVALID_REQUEST"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El criterio de ordenamiento solicitado no es válido.",
            code=self.code,
        )


class InvalidFilterError(UnprocessableEntityError):
    """El valor de un filtro de la superficie administrativa no es válido.

    Un filtro es válido cuando su valor pertenece al vocabulario del dominio
    (`estado`, `tipo`, `rol`, `resultado`, ...) o cuando tiene la forma
    esperada (UUID, fecha ISO, booleano). Un valor fuera del vocabulario se
    rechaza con 422 `INVALID_REQUEST`: nunca se aplica un valor arbitrario al
    queryset ni se responde con un error 500.

    Un identificador bien formado que NO existe NO es un error de filtro: es un
    filtro que no matchea ninguna fila, y la lista responde vacía.

    El mensaje público sale del catálogo; esta excepción no interpola el valor
    recibido (podría contener basura del cliente).
    """

    code: str = "INVALID_REQUEST"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Alguno de los filtros enviados no es válido.",
            code=self.code,
        )


class AdminResourceNotFoundError(NotFoundError):
    """El recurso solicitado no existe o no pertenece al evento activo (404).

    Un id desconocido y un id que pertenece a OTRA edición del evento se
    responden IGUAL: 404 `RESOURCE_NOT_FOUND`. La administración nunca revela
    la existencia de un recurso fuera de su alcance con un 403, que confirmaría
    que el id existe.

    El mensaje público sale del catálogo `core/exceptions.py::PUBLIC_ERROR_MESSAGES`;
    esta excepción no interpola identificadores internos.
    """

    code: str = "RESOURCE_NOT_FOUND"

    def __init__(self, resource: str = "Recurso"):
        self.code = self.code
        super().__init__(resource=resource, code=self.code)


__all__ = [
    "EventoActivoNoEncontradoError",
    "InvalidOrderingError",
    "InvalidFilterError",
    "AdminResourceNotFoundError",
]
