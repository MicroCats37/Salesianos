"""Domain exceptions for usuarios external document lookup."""

from core.exceptions import NotFoundError, UnprocessableEntityError


class SunatNotFoundError(NotFoundError):
    """Excepción cuando un RUC no es encontrado en SUNAT."""

    code: str = "SUNAT_NOT_FOUND"

    def __init__(self, ruc: str):
        self.code = self.code
        super().__init__(404, f"RUC {ruc} no encontrado en SUNAT")


class ReniecNotFoundError(NotFoundError):
    """Excepción cuando un DNI no es encontrado en RENIEC."""

    code: str = "RENIEC_NOT_FOUND"

    def __init__(self, dni: str):
        self.code = self.code
        super().__init__(404, f"DNI {dni} no encontrado en RENIEC")


class PersonaNoEncontradaError(NotFoundError):
    """
    Excepción cuando el documento consultado NO corresponde a una `Persona`
    registrada (404).

    Es el ÚNICO error del resolver de identidad: la coincidencia es EXACTA y
    la ausencia de la persona es un "no encontrado", nunca una lista ni una
    creación. El mensaje público sale del catálogo de `core/exceptions.py`.
    """

    code: str = "PERSONA_NO_ENCONTRADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            404,
            "No se encontró una persona registrada con el documento consultado.",
        )


class TipoDocumentoInvalidoError(UnprocessableEntityError):
    """
    Excepción cuando el tipo de documento NO pertenece al vocabulario cerrado
    del módulo de identidad (422).

    El tipo es parte de la identidad: un tipo desconocido es una petición
    inválida (categoría "Validation"), NO una persona que no existe. Un tipo
    VÁLIDO sin persona registrada sigue siendo un 404.
    """

    code: str = "TIPO_DOCUMENTO_INVALIDO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "El tipo de documento consultado no es válido.",
            code=self.code,
        )
