"""Hidrata el cuerpo JSON de la sala de proyección.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.8 ·
         `contract/api-wrapper-presenter-contract.md` §8

**POR QUÉ un hidrator y no un parámetro de cuerpo tipado.** Cuando el
controller declara el cuerpo como un parámetro (`payload: CrearVideoIn`),
Django Ninja envuelve el schema en un modelo cuyo campo se llama como el
parámetro, y el error de validación viaja como `payload.titulo`. El frontend
mapea los errores de campo por nombre EXACTO (`setError("titulo")`), así que
un prefijo de transporte rompe el formulario de administración.

El hidrator valida el JSON CRUDO contra el schema: el error de pydantic
travela con la ruta del payload (`titulo`, `url`, `descripcion`) y el
handler global de `core/exceptions.py` lo convierte en un 422 con
`error.field_errors`.

Es el mismo patrón que usan `modules/marketplace` y `modules/patrocinadores`
para el mismo problema.

Precedencia de errores:

1. cuerpo ausente o con JSON inválido → 422 `VALIDATION_ERROR`;
2. payload que no valida contra el schema → 422 `VALIDATION_ERROR` con los
   errores POR CAMPO en `error.field_errors`.
"""

import json

from pydantic import ValidationError as PydanticValidationError

from core.exceptions import UnprocessableEntityError

from modules.videos.presentation.schemas.videos_schemas import (
    ActualizarVideoIn,
    CrearVideoIn,
)


class VideoHydrator:
    """Construye los schemas HTTP de la sala de proyección desde la petición."""

    @staticmethod
    def payload_crudo(request) -> dict:
        """El JSON del cuerpo de la petición, como `dict`."""
        cuerpo = request.body
        if not cuerpo:
            raise UnprocessableEntityError(
                "El cuerpo de la petición es obligatorio.",
                code="VALIDATION_ERROR",
            )

        try:
            texto = cuerpo.decode("utf-8")
        except UnicodeDecodeError:
            raise UnprocessableEntityError(
                "El cuerpo de la petición no es JSON válido.",
                code="VALIDATION_ERROR",
            ) from None

        try:
            crudo = json.loads(texto)
        except (TypeError, ValueError):
            raise UnprocessableEntityError(
                "El cuerpo de la petición no es JSON válido.",
                code="VALIDATION_ERROR",
            ) from None

        if not isinstance(crudo, dict):
            raise UnprocessableEntityError(
                "El cuerpo de la petición debe contener un objeto JSON.",
                code="VALIDATION_ERROR",
            )

        return crudo

    # ── Hidratación ─────────────────────────────────────────────────────────

    @staticmethod
    def _validar(schema, payload):
        """Convierte errores del schema en rutas de campo del propio video."""
        try:
            return schema.model_validate(payload)
        except PydanticValidationError as exc:
            raise UnprocessableEntityError(
                exc.errors(include_input=False),
                code="VALIDATION_ERROR",
            ) from None

    @classmethod
    def hydrate_crear(cls, request) -> CrearVideoIn:
        """El payload de alta, validado contra `CrearVideoIn`."""
        return cls._validar(CrearVideoIn, cls.payload_crudo(request))

    @classmethod
    def hydrate_actualizar(cls, request) -> ActualizarVideoIn:
        """El payload de edición, validado contra `ActualizarVideoIn`."""
        return cls._validar(ActualizarVideoIn, cls.payload_crudo(request))


__all__ = ["VideoHydrator"]
