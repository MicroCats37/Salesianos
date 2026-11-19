"""Hidrata el payload `data` + `files` del protocolo multipart de media.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`
Contract: `contract/api-wrapper-presenter-contract.md` §2 ·
          `contract/django-app-architecture-contract.md` §4.8

PROTOCOLO (FR-06 §2.4, congelado):

| Parte | Nombre | Contenido |
|---|---|---|
| Datos | campo `data` | JSON del payload, con cada `File` sustituido por su token |
| Archivos | campo `files` | una o más partes; el `filename` es `<token>___<realname>` |

Este módulo CONSUME las primitivas de `core/media.py` (FND-01). NO usa los
helpers heredados `core/types.py::hydrate_form` ni `parse_request_payload`:
esos lanzan `HttpError` con texto interpolado y no usan los códigos de media
del catálogo público.

Precedencia de errores (decidida aquí, de forma explícita):

1. `data` ausente o con JSON inválido → 422 `VALIDATION_ERROR`;
2. token sin parte, parte sin token, token repetido → 400 `MEDIA_*`;
3. payload que no valida contra el schema → 422 `VALIDATION_ERROR`;
4. firma, MIME o tamaño inválidos → 400/413 `MEDIA_*`.

El MATCHING es EXACTAMENTE UNA VEZ: `core.media.resolver_tokens_media`
devuelve un diccionario indexado por token y rechaza el token repetido, el
token sin parte y la parte sin token.
"""

import json
import logging

from core.exceptions import UnprocessableEntityError
from core.media import (
    parsear_archivos_media,
    resolver_tokens_media,
    validar_archivo_media,
)

from modules.marketplace.domain.schemas.producto_schemas import (
    ImagenProductoData,
    ImagenProductoUploadData,
    ProductoCreateData,
)
from modules.marketplace.presentation.schemas.producto_schemas import CrearProductoIn

logger = logging.getLogger(__name__)


class ProductoHydrator:
    """Construye el DTO de alta de un producto desde la petición HTTP."""

    # ── Lectura del payload ─────────────────────────────────────────────────

    @staticmethod
    def _es_multipart(request) -> bool:
        content_type = request.META.get("CONTENT_TYPE", "") or ""
        return "multipart" in content_type

    @classmethod
    def payload_crudo(cls, request) -> dict:
        """El JSON del campo `data` (multipart) o del cuerpo (JSON)."""
        if cls._es_multipart(request):
            data_str = request.POST.get("data")
            if data_str is None:
                raise UnprocessableEntityError(
                    "El campo 'data' es obligatorio.",
                    code="VALIDATION_ERROR",
                )
            return cls._json(data_str)

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
        return cls._json(texto)

    @staticmethod
    def _json(texto) -> dict:
        try:
            crudo = json.loads(texto)
        except (TypeError, ValueError):
            raise UnprocessableEntityError(
                "El campo 'data' no contiene JSON válido.",
                code="VALIDATION_ERROR",
            ) from None
        if not isinstance(crudo, dict):
            raise UnprocessableEntityError(
                "El campo 'data' debe contener un objeto JSON.",
                code="VALIDATION_ERROR",
            )
        return crudo

    # ── Hidratación ─────────────────────────────────────────────────────────

    @classmethod
    def hydrate(cls, request) -> ProductoCreateData:
        """Hidrata la petición y devuelve el DTO de alta del producto.

        El DTO lleva LA REPRESENTACIÓN ÚNICA de cada archivo
        (`ImagenProductoUploadData`): el controller no vuelve a recibir los
        archivos por otro camino y el flujo no los vuelve a pedir.
        """
        crudo = cls.payload_crudo(request)

        archivos = parsear_archivos_media(request.FILES)
        resueltos = resolver_tokens_media(crudo, archivos)

        datos = CrearProductoIn.model_validate(crudo)

        imagenes = []
        for declarada in datos.imagenes:
            archivo = resueltos[declarada.token]
            validado = validar_archivo_media(archivo)
            imagenes.append(
                ImagenProductoData(
                    token=declarada.token,
                    es_principal=declarada.es_principal,
                    texto_alternativo=declarada.texto_alternativo,
                    upload=ImagenProductoUploadData(
                        token=declarada.token,
                        archivo=archivo,
                        mime_detectado=validado.mime_detectado,
                        extension=validado.extension,
                        tamano=validado.tamano,
                        nombre_original=validado.nombre_original,
                    ),
                )
            )

        return ProductoCreateData(
            edicion_id=cls._edicion_placeholder(),
            nombre=datos.nombre,
            slug=datos.slug,
            descripcion=datos.descripcion,
            categoria_id=datos.categoria_id,
            precio=datos.precio,
            precio_oferta=datos.precio_oferta,
            oferta_inicia=datos.oferta_inicia,
            oferta_termina=datos.oferta_termina,
            estado=datos.estado,
            imagenes=imagenes,
        )

    @staticmethod
    def _edicion_placeholder():
        """Identificador de edición provisional.

        El alcance lo RESUELVE el servidor (orquestador): el cliente nunca
        elige la edición a la que escribe. Este valor se sustituye allí.
        """
        from uuid import UUID

        return UUID(int=0)
