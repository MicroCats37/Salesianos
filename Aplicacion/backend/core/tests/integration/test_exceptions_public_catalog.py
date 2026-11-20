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


# ── Códigos mergeados por DOM-03 (reconciliación A0) ─────────────────────────
#
# A0-03 y A0-04 del paquete DOM-03 (pases, beneficiarios y cortesía): catorce
# códigos públicos. CUATRO ya estaban catalogados (`PASE_NO_DISPONIBLE`,
# `PASE_NO_ENCONTRADO`, `PASE_NO_TRANSFERIBLE`,
# `PASE_BENEFICIARIO_NO_ENCONTRADO`): NO se duplicaron, se ratificaron.
#
# La prosa pública la decide A0 y NO puede interpolar identificadores, slugs,
# precios, rutas ni texto crudo (`contract/api-wrapper-presenter-contract.md`
# §8).

CODIGOS_DOM03 = (
    # 409 — el pase no se puede comprar (CONGELADO por `FR-07` §3.3).
    "PASE_NO_DISPONIBLE",
    # 422 — la cantidad de pases no es válida (CONGELADO por `FR-07` §3.3).
    "CANTIDAD_INVALIDA",
    # 404 — el pase no existe o no pertenece a la edición.
    "PASE_NO_ENCONTRADO",
    # 404 — la compra de pases no existe.
    "COMPRA_PASE_NO_ENCONTRADA",
    # 404 — el beneficiario no existe en la compra (CONGELADO por `FR-07` §3.3).
    "PASE_BENEFICIARIO_NO_ENCONTRADO",
    # 409 — el derecho no admite la operación (CONGELADO por `FR-07` §3.3).
    "PASE_NO_TRANSFERIBLE",
    # 409 — la persona ya tiene un derecho activo de ese pase.
    "PASE_DUPLICADO",
    # 409 — el lote no tiene capacidad pagada libre.
    "SIN_PASES_DISPONIBLES",
    # 409 — una compra pendiente NO habilita pases.
    "COMPRA_PASE_NO_PAGADA",
    # 401 — el enlace de gestión no es válido (credencial).
    "TOKEN_PASE_INVALIDO",
    # 401 — la operación exige una cuenta autenticada.
    "ACTOR_REQUERIDO",
    # 403 — el actor no es el titular de la compra.
    "COMPRA_PASE_NO_AUTORIZADA",
    # 422 — el motivo de la cortesía es obligatorio.
    "CORTESIA_MOTIVO_INVALIDO",
    # 404 — la cortesía no existe.
    "CORTESIA_NO_ENCONTRADA",
)

#: Código → status esperado. El status lo DECIDE la clase de excepción del
#: dominio: el catálogo sólo aporta la prosa. La aserción de abajo lo comprueba
#: contra la clase real, así que catálogo y dominio no pueden divergir.
STATUS_DOM03 = {
    "PASE_NO_DISPONIBLE": 409,
    "CANTIDAD_INVALIDA": 422,
    "PASE_NO_ENCONTRADO": 404,
    "COMPRA_PASE_NO_ENCONTRADA": 404,
    "PASE_BENEFICIARIO_NO_ENCONTRADO": 404,
    "PASE_NO_TRANSFERIBLE": 409,
    "PASE_DUPLICADO": 409,
    "SIN_PASES_DISPONIBLES": 409,
    "COMPRA_PASE_NO_PAGADA": 409,
    "TOKEN_PASE_INVALIDO": 401,
    "ACTOR_REQUERIDO": 401,
    "COMPRA_PASE_NO_AUTORIZADA": 403,
    "CORTESIA_MOTIVO_INVALIDO": 422,
    "CORTESIA_NO_ENCONTRADA": 404,
}

#: Códigos mergeados por DOM-02 (A0-DOM02-03) que quedaron PENDIENTES y se
#: absorben en esta reconciliación: la misma raíz compartida
#: (`salesianos_fest`) y `CUPO_INVALIDO` está CONGELADO por `FR-07` §3.3 para
#: `RT-CM-01`, que es una ruta VIVA. `PERSONA_NO_ENCONTRADA` ya estaba
#: catalogado por FND-03: no se duplicó.
CODIGOS_DOM02 = (
    "CUPO_INVALIDO",
    "SIN_CUPOS_DISPONIBLES",
    "PARTICIPANTE_NO_ELEGIBLE",
    "PARTICIPANTE_DUPLICADO",
    "EQUIPO_COMPLETO",
    "PARTICIPANTE_NO_ENCONTRADO",
    "EQUIPO_NO_ENCONTRADO",
)

STATUS_DOM02 = {
    "CUPO_INVALIDO": 422,
    "SIN_CUPOS_DISPONIBLES": 409,
    "PARTICIPANTE_NO_ELEGIBLE": 422,
    "PARTICIPANTE_DUPLICADO": 422,
    "EQUIPO_COMPLETO": 409,
    "PARTICIPANTE_NO_ENCONTRADO": 404,
    "EQUIPO_NO_ENCONTRADO": 404,
}

CODIGOS_A0R3 = CODIGOS_DOM03 + CODIGOS_DOM02


@pytest.mark.parametrize("codigo", CODIGOS_A0R3)
def test_los_codigos_de_dom03_y_dom02_estan_en_el_catalogo(codigo):
    """Cada código público del paquete tiene prosa en el catálogo."""
    assert codigo in PUBLIC_ERROR_MESSAGES
    assert PUBLIC_ERROR_MESSAGES[codigo]


@pytest.mark.parametrize("codigo", CODIGOS_A0R3)
def test_la_prosa_de_los_codigos_de_dom03_y_dom02_es_prosa_fija(codigo):
    """La prosa pública no interpola nada: es texto fijo y seguro."""
    mensaje = PUBLIC_ERROR_MESSAGES[codigo]

    assert "{" not in mensaje
    assert "}" not in mensaje
    assert "%" not in mensaje
    assert "$" not in mensaje


@pytest.mark.parametrize("codigo,status", sorted(STATUS_DOM03.items()))
def test_cada_codigo_de_dom03_responde_con_el_status_pedido(codigo, status):
    """El status lo fija la clase de excepción del dominio, no la prosa."""
    from core.exceptions import public_message_for

    assert public_message_for(codigo, status) == PUBLIC_ERROR_MESSAGES[codigo]


@pytest.mark.parametrize("codigo,status", sorted(STATUS_DOM02.items()))
def test_cada_codigo_de_dom02_responde_con_el_status_pedido(codigo, status):
    """El status lo fija la clase de excepción del dominio, no la prosa."""
    from core.exceptions import public_message_for

    assert public_message_for(codigo, status) == PUBLIC_ERROR_MESSAGES[codigo]


@pytest.mark.parametrize(
    "nombre_excepcion,codigo,status",
    [
        ("PaseNoDisponibleError", "PASE_NO_DISPONIBLE", 409),
        ("CantidadInvalidaError", "CANTIDAD_INVALIDA", 422),
        ("PaseNoEncontradoError", "PASE_NO_ENCONTRADO", 404),
        ("CompraPaseNoEncontradaError", "COMPRA_PASE_NO_ENCONTRADA", 404),
        (
            "PaseBeneficiarioNoEncontradoError",
            "PASE_BENEFICIARIO_NO_ENCONTRADO",
            404,
        ),
        ("PaseNoTransferibleError", "PASE_NO_TRANSFERIBLE", 409),
        ("PaseDuplicadoError", "PASE_DUPLICADO", 409),
        ("SinPasesDisponiblesError", "SIN_PASES_DISPONIBLES", 409),
        ("CompraPaseNoPagadaError", "COMPRA_PASE_NO_PAGADA", 409),
        ("TokenPaseInvalidoError", "TOKEN_PASE_INVALIDO", 401),
        ("ActorRequeridoError", "ACTOR_REQUERIDO", 401),
        ("CompraPaseNoAutorizadaError", "COMPRA_PASE_NO_AUTORIZADA", 403),
        ("CortesiaMotivoInvalidoError", "CORTESIA_MOTIVO_INVALIDO", 422),
        ("CortesiaNoEncontradaError", "CORTESIA_NO_ENCONTRADA", 404),
    ],
)
def test_el_status_del_codigo_es_el_de_la_clase_de_dominio(
    nombre_excepcion,
    codigo,
    status,
):
    """El catálogo y la clase de dominio NO pueden divergir.

    La prosa la elige A0; el status lo fija la excepción que el dominio
    lanza. Este test ata las dos cosas: si una clase cambia de status, el
    catálogo tiene que cambiar con ella.
    """
    from importlib import import_module

    dominio = import_module("modules.salesianos_fest.domain.exceptions")
    exccepcion = getattr(dominio, nombre_excepcion)()

    assert exccepcion.code == codigo
    assert exccepcion.status_code == status
    assert codigo in PUBLIC_ERROR_MESSAGES


@pytest.mark.parametrize(
    "nombre_excepcion,codigo,status",
    [
        ("CupoInvalidoError", "CUPO_INVALIDO", 422),
        ("SinCuposDisponiblesError", "SIN_CUPOS_DISPONIBLES", 409),
        ("ParticipanteNoElegibleError", "PARTICIPANTE_NO_ELEGIBLE", 422),
        ("ParticipanteDuplicadoError", "PARTICIPANTE_DUPLICADO", 422),
        ("EquipoCompletoError", "EQUIPO_COMPLETO", 409),
        ("ParticipanteNoEncontradoError", "PARTICIPANTE_NO_ENCONTRADO", 404),
        ("EquipoNoEncontradoError", "EQUIPO_NO_ENCONTRADO", 404),
    ],
)
def test_el_status_del_codigo_de_dom02_es_el_de_la_clase_de_dominio(
    nombre_excepcion,
    codigo,
    status,
):
    """Misma invariante para los códigos absorbidos de DOM-02."""
    from importlib import import_module

    dominio = import_module("modules.salesianos_fest.domain.exceptions")
    exccepcion = getattr(dominio, nombre_excepcion)()

    assert exccepcion.code == codigo
    assert exccepcion.status_code == status
    assert codigo in PUBLIC_ERROR_MESSAGES


# ── Barrido del catálogo (cierre del cableado global) ───────────────────────
#
# Las listas explícitas de arriba comprueban los códigos que A0 conoce de uno
# en uno. El BARRIDO de abajo comprueba la INVARIANTE: TODO código que declara
# una clase de excepción de dominio tiene prosa en el catálogo público.
#
# Sin este barrido, un módulo nuevo (o un código nuevo dentro de un módulo
# existente) puede declarar un código sin catalogar: el cliente recibiría el
# mensaje GENÉRICO del status y no podría distinguir la causa del síntoma
# (`FR-01` §4.4). El barrido es lo que convierte "el catálogo está
# sincronizado" en un hecho VERIFICADO y no en una afirmación.


#: Módulos de dominio con clases de excepción propias. Cada uno declara sus
#: códigos estables en el atributo de clase `code`.
MODULOS_DE_EXCEPCIONES = (
    "modules.competencias.domain.exceptions",
    "modules.marketplace.domain.exceptions",
    "modules.patrocinadores.domain.exceptions",
    "modules.salesianos_fest.domain.exceptions",
    "modules.usuarios.domain.exceptions",
    "modules.validaciones.domain.exceptions",
    "modules.videos.domain.exceptions",
)


def _codigos_de_dominio():
    """`(codigo, origen)` de cada clase de excepción de los módulos listados."""
    import inspect
    from importlib import import_module

    encontrados = []
    for nombre in MODULOS_DE_EXCEPCIONES:
        modulo = import_module(nombre)
        for atributo in vars(modulo).values():
            if not inspect.isclass(atributo):
                continue
            code = getattr(atributo, "code", None)
            if not isinstance(code, str) or not code.isupper():
                continue
            encontrados.append((code, f"{nombre}.{atributo.__name__}"))
    return encontrados


def test_todo_codigo_de_dominio_esta_en_el_catalogo_publico():
    """Ningún código de dominio se queda SIN prosa: el barrido no admite huecos."""
    faltantes = sorted(
        f"{origen} → {code}"
        for code, origen in _codigos_de_dominio()
        if code not in PUBLIC_ERROR_MESSAGES
    )

    assert not faltantes, f"Códigos sin catalogar: {faltantes}"


def test_la_prosa_de_todo_codigo_de_dominio_es_prosa_fija():
    """La prosa del catálogo no interpola nada: es texto fijo y seguro."""
    interpolaciones = sorted(
        f"{code}: {PUBLIC_ERROR_MESSAGES[code]}"
        for code, _ in _codigos_de_dominio()
        if code in PUBLIC_ERROR_MESSAGES
        and any(marca in PUBLIC_ERROR_MESSAGES[code] for marca in ("{", "}", "%", "$"))
    )

    assert not interpolaciones, f"Prosa interpolada: {interpolaciones}"


# ── Cotización (A0 · residual R-2 de VER-01, 2026-11-20) ────────────────────
#
# `PrecioCambiadoError` (409) lo declara
# `modules.salesianos_fest.domain.exceptions` y PIDE su prosa a A0 ("Código
# REQUESTED a A0"). Sin catálogo, la respuesta cae al mensaje GENÉRICO del
# status 409 ("Conflicto con el estado actual del recurso.") y el cliente no
# puede distinguir "el precio se movió" de cualquier otro conflicto.
#
# La prosa la elige A0 y NO puede interpolar precios, importes, ids ni slugs.


CODIGOS_COTIZACION = ("PRECIO_CAMBIADO",)


@pytest.mark.parametrize("codigo", CODIGOS_COTIZACION)
def test_los_codigos_de_cotizacion_estan_en_el_catalogo(codigo):
    """Cada código de cotización tiene prosa en el catálogo público."""
    assert codigo in PUBLIC_ERROR_MESSAGES
    assert PUBLIC_ERROR_MESSAGES[codigo]


@pytest.mark.parametrize("codigo", CODIGOS_COTIZACION)
def test_la_prosa_de_los_codigos_de_cotizacion_es_prosa_fija(codigo):
    """La prosa pública no interpola nada: es texto fijo y seguro."""
    mensaje = PUBLIC_ERROR_MESSAGES[codigo]

    assert "{" not in mensaje
    assert "}" not in mensaje
    assert "%" not in mensaje
    assert "$" not in mensaje


@pytest.mark.parametrize(
    "nombre_excepcion,codigo,status",
    [
        ("PrecioCambiadoError", "PRECIO_CAMBIADO", 409),
    ],
)
def test_el_status_del_codigo_de_cotizacion_es_el_de_la_clase_de_dominio(
    nombre_excepcion,
    codigo,
    status,
):
    """Catálogo y clase de dominio NO pueden divergir.

    El status lo fija la excepción que el dominio lanza; la prosa la elige A0.
    """
    from importlib import import_module

    dominio = import_module("modules.salesianos_fest.domain.exceptions")
    excepcion = getattr(dominio, nombre_excepcion)()

    assert excepcion.code == codigo
    assert excepcion.status_code == status
    assert codigo in PUBLIC_ERROR_MESSAGES
