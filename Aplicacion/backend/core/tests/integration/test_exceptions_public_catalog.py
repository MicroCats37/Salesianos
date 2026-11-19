"""Traducción de excepciones al envelope HTTP (FREEZE-ENV-1.0.0 · FR-01 §4.4).

GIVEN  los handlers globales registrados por `core.exceptions`
WHEN   ocurre una excepción de cada categoría HTTP congelada
THEN   la respuesta es segura (nada de texto crudo), tipada (código estable)
       y con la forma del envelope único.
"""

import json

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import RequestFactory
from ninja.errors import HttpError
from ninja_extra.exceptions import (
    AuthenticationFailed as NinjaExtraAuthenticationFailed,
    PermissionDenied as NinjaExtraPermissionDenied,
)
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from core.exceptions import PUBLIC_ERROR_MESSAGES


@pytest.fixture
def request_falso():
    return RequestFactory().post("/api/prueba")


def _invocar(api, exc, request_falso):
    """Ejecuta el handler registrado para la clase de la excepción.

    La búsqueda recorre el MRO: las excepciones de dominio heredan de
    `HttpError` y su handler es el de `HttpError`.
    """
    handler = None
    for klass in type(exc).__mro__:
        handler = api._exception_handlers.get(klass)
        if handler is not None:
            break
    assert handler is not None, f"no hay handler para {type(exc).__name__}"

    response = handler(request_falso, exc)
    return response.status_code, json.loads(response.content)


# ── 401 — autenticación ──────────────────────────────────────────────────────


def test_401_usa_el_codigo_y_el_mensaje_del_catalogo(api, request_falso):
    status, body = _invocar(
        api, NinjaExtraAuthenticationFailed("token inválido"), request_falso
    )

    assert status == 401
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"] is None
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert body["error"]["message"] == PUBLIC_ERROR_MESSAGES["AUTHENTICATION_REQUIRED"]


def test_401_no_expone_el_token_que_fallo(api, request_falso):
    _, body = _invocar(
        api,
        NinjaExtraAuthenticationFailed("Bearer eyJhbGciOiJIUzI1NiJ9.secreto"),
        request_falso,
    )

    assert "secreto" not in json.dumps(body)


# ── 403 — autorización ───────────────────────────────────────────────────────


def test_403_usa_el_codigo_y_el_mensaje_del_catalogo(api, request_falso):
    status, body = _invocar(
        api, NinjaExtraPermissionDenied("regla interna de autorización"), request_falso
    )

    assert status == 403
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert body["error"]["message"] == PUBLIC_ERROR_MESSAGES["ACTION_NOT_ALLOWED"]


def test_403_no_expone_la_regla_interna(api, request_falso):
    _, body = _invocar(
        api,
        NinjaExtraPermissionDenied("requiere la capacidad admin.pagos.aprobar"),
        request_falso,
    )

    assert "admin.pagos.aprobar" not in json.dumps(body)


# ── 404 — recurso inexistente ────────────────────────────────────────────────


def test_404_usa_el_codigo_y_el_mensaje_del_catalogo(api, request_falso):
    status, body = _invocar(api, HttpError(404, "recurso interno 42"), request_falso)

    assert status == 404
    assert body["error"]["code"] == "HTTP_ERROR"
    assert body["error"]["message"] == "No se encontró el recurso solicitado."
    assert "42" not in json.dumps(body)


# ── 409 — conflicto de negocio ───────────────────────────────────────────────


def test_409_usa_el_codigo_y_el_mensaje_del_catalogo(api, request_falso):
    from core.exceptions import ConflictError

    status, body = _invocar(
        api, ConflictError("ya existe", code="COMPETENCIA_DUPLICADA"), request_falso
    )

    assert status == 409
    assert body["error"]["code"] == "COMPETENCIA_DUPLICADA"
    assert body["error"]["message"] == PUBLIC_ERROR_MESSAGES["COMPETENCIA_DUPLICADA"]


# ── 422 — validación ─────────────────────────────────────────────────────────


class _Payload(BaseModel):
    codigo: str = Field(min_length=5)
    edad: int


def _error_de_payload():
    try:
        _Payload(codigo="ab", edad="no-es-un-numero")
    except PydanticValidationError as exc:
        return exc
    raise AssertionError("el payload inválido debió producir un error")


def test_422_trae_los_errores_por_campo_en_field_errors(api, request_falso):
    status, body = _invocar(api, _error_de_payload(), request_falso)

    assert status == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == PUBLIC_ERROR_MESSAGES["VALIDATION_ERROR"]

    fields = {entry["field"] for entry in body["error"]["field_errors"]}
    assert fields == {"codigo", "edad"}
    for entry in body["error"]["field_errors"]:
        assert entry["code"]
        assert entry["message"]


def test_422_no_usa_details_como_canal_de_error_por_campo(api, request_falso):
    _, body = _invocar(api, _error_de_payload(), request_falso)

    details = body["error"]["details"] or {}
    assert "codigo" not in details
    assert "edad" not in details


def test_422_de_django_no_expone_el_valor_que_fallo(api, request_falso):
    exc = DjangoValidationError({"email": ["Ya existe 'correo@secreto.pe'."]})

    status, body = _invocar(api, exc, request_falso)

    assert status == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "correo@secreto.pe" not in json.dumps(body)
    assert body["error"]["field_errors"][0]["field"] == "email"


# ── 500 — error inesperado ───────────────────────────────────────────────────


def test_500_no_expone_el_texto_crudo_de_la_excepcion(api, request_falso):
    status, body = _invocar(
        api, Exception("Traceback: password=hunter2"), request_falso
    )

    assert status == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == PUBLIC_ERROR_MESSAGES["INTERNAL_ERROR"]
    assert "hunter2" not in json.dumps(body)


def test_un_value_error_no_expone_su_texto_crudo(api, request_falso):
    status, body = _invocar(
        api, ValueError("credencial=hunter2"), request_falso
    )

    assert status == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "hunter2" not in json.dumps(body)


# ── Reglas transversales ─────────────────────────────────────────────────────


def test_un_codigo_no_catalogado_nunca_devuelve_el_mensaje_original(api, request_falso):
    status, body = _invocar(
        api, HttpError(400, "detalle interno que no debe salir"), request_falso
    )

    assert status == 400
    assert body["error"]["message"] != "detalle interno que no debe salir"
    assert body["error"]["message"] == "La solicitud no es válida."


def test_los_codigos_de_multimedia_estan_en_el_catalogo_publico():
    for codigo in (
        "MEDIA_TIPO_NO_PERMITIDO",
        "MEDIA_TAMANO_EXCEDIDO",
        "MEDIA_TOKEN_NO_RESUELTO",
        "MEDIA_ARCHIVO_HUERFANO",
        "MEDIA_TOKEN_DUPLICADO",
    ):
        assert codigo in PUBLIC_ERROR_MESSAGES
        assert PUBLIC_ERROR_MESSAGES[codigo]


def test_todos_los_mensajes_del_catalogo_son_texto_no_vacio():
    for codigo, mensaje in PUBLIC_ERROR_MESSAGES.items():
        assert mensaje, codigo
        assert isinstance(mensaje, str)


# ── Códigos mergeados por DOM-01 y DOM-04 (reconciliación A0) ───────────────
#
# A0-03 de DOM-01 y A0-06 de DOM-04: los códigos viajan estables en
# `error.code`; sin prosa en el catálogo la respuesta cae al mensaje genérico
# del status (F-21). La prosa pública la decide A0 y NO puede interpolar
# identificadores, slugs, precios, rutas ni texto crudo.


CODIGOS_DOM01 = (
    "PAQUETE_NO_VIGENTE",
    "DISCIPLINA_NO_PERMITIDA",
    "EQUIPO_DUPLICADO",
    "INSCRIPCION_NO_ENCONTRADA",
    "INSCRIPCION_NO_AUTORIZADA",
    "COMPRADOR_SIN_PERSONA",
)

CODIGOS_DOM04 = (
    "PRODUCTO_NO_ENCONTRADO",
    "PRODUCTO_SLUG_DUPLICADO",
    "PRODUCTO_NO_DISPONIBLE",
    "PRODUCTO_CATEGORIA_INCOHERENTE",
    "CATEGORIA_PRODUCTO_NO_ENCONTRADA",
    "CATEGORIA_PRODUCTO_SLUG_DUPLICADO",
    "PRODUCTO_IMAGEN_NO_ENCONTRADA",
    "OFERTA_INVALIDA",
    "GALERIA_INVALIDA",
)

CODIGOS_MERGEADOS = CODIGOS_DOM01 + CODIGOS_DOM04


@pytest.mark.parametrize("codigo", CODIGOS_MERGEADOS)
def test_los_codigos_de_dom01_y_dom04_estan_en_el_catalogo(codigo):
    assert codigo in PUBLIC_ERROR_MESSAGES
    assert PUBLIC_ERROR_MESSAGES[codigo]


@pytest.mark.parametrize("codigo", CODIGOS_MERGEADOS)
def test_la_prosa_de_los_codigos_nuevos_es_prosa_fija(codigo):
    """La prosa pública no interpola nada: es texto fijo y seguro."""
    mensaje = PUBLIC_ERROR_MESSAGES[codigo]

    assert "{" not in mensaje
    assert "}" not in mensaje
    assert "%" not in mensaje
    assert "$" not in mensaje


@pytest.mark.parametrize(
    "codigo,status",
    [
        ("PAQUETE_NO_VIGENTE", 409),
        ("DISCIPLINA_NO_PERMITIDA", 422),
        ("EQUIPO_DUPLICADO", 422),
        ("INSCRIPCION_NO_ENCONTRADA", 404),
        ("INSCRIPCION_NO_AUTORIZADA", 403),
        ("COMPRADOR_SIN_PERSONA", 422),
        ("PRODUCTO_NO_ENCONTRADO", 404),
        ("PRODUCTO_SLUG_DUPLICADO", 409),
        ("PRODUCTO_NO_DISPONIBLE", 409),
        ("PRODUCTO_CATEGORIA_INCOHERENTE", 422),
        ("CATEGORIA_PRODUCTO_NO_ENCONTRADA", 404),
        ("CATEGORIA_PRODUCTO_SLUG_DUPLICADO", 409),
        ("PRODUCTO_IMAGEN_NO_ENCONTRADA", 404),
        ("OFERTA_INVALIDA", 422),
        ("GALERIA_INVALIDA", 422),
    ],
)
def test_cada_codigo_nuevo_responde_con_el_status_pedido(codigo, status):
    """El status lo fija la clase de excepción del dominio, no la prosa."""
    from core.exceptions import public_message_for

    assert public_message_for(codigo, status) == PUBLIC_ERROR_MESSAGES[codigo]
