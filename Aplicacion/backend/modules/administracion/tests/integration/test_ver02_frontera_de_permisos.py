"""VER-02 — La frontera de permisos, RECORRIDA sobre todas las rutas vivas.

Packet: `VER-02` · Change: `salesianos-fest-rebuild` · Owner: A9
Freeze: `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0`

GIVEN  el registro vivo de la API (75 rutas · 79 operaciones)
WHEN   se recorre TODA operación protegida por JWT con una petición ANÓNIMA
THEN   ninguna responde 2xx: la autenticación se exige ANTES que el permiso
        (401 `AUTHENTICATION_REQUIRED`) y la denegación NO filtra trazas,
        rutas, SQL ni identificadores internos.

AND    con una cuenta NORMAL (grupo `Normal`, sin ninguna capacidad), toda
        superficie que exige capacidad administrativa responde 403.

AND    las rutas cuyo credencial es un TOKEN (lote de pases, pedido) responden
        404 a un token ajeno: la denegación es NEUTRA y no revela la existencia
        del recurso.

AND    la lista CONGELADA de operaciones públicas es EXACTAMENTE la que el
        registro expone: una ruta nueva no puede volverse pública sin que este
        guardián lo detecte y lo devuelva a su dueño.

Este archivo NO reescribe el inventario: lo DERIVA del registro vivo. Lo único
congelado es el conjunto de las operaciones públicas, porque ése es el único
conjunto que una decisión de producto puede cambiar sin querer.

`FREEZE-TC-1.0.0`: los controllers son `async def`; el cliente es
`django.test.Client`, que lo soporta.
"""

import json
import uuid

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

#: Estas pruebas tocan la base de datos: las rutas con token la consultan
#: para decidir si el recurso existe.
pytestmark = pytest.mark.django_db

#: Identificador que satisface cualquier conversor de ruta por UUID o por
#: texto. No existe ningún recurso con este identificador, de modo que un 404
#: sólo puede significar "no existe" o "no es tuyo": nunca "existe y te lo
#: niego" con datos adjuntos.
ID_QUE_NO_EXISTE = "11111111-2222-3333-4444-555555555555"

#: Operaciones del registro vivo que NO exigen credencial de sesión.
#:
#: Criterio de la lista: o bien son públicas por contrato (catálogos, login,
#: alta de cuenta), o bien su credencial es OTRO cosa —un token en la ruta o
#: una firma del proveedor— y por eso NO aparecen con `security` en el
#: esquema. Las tres operaciones de `/api/token/**` pertenecen a `ninja_jwt`,
#: un controller de terceros: su autenticación es la propia de la biblioteca.
OPERACIONES_PUBLICAS_CONGELADAS = frozenset(
    {
        # Autenticación y alta de cuenta.
        ("POST", "/api/auth/login/dni"),
        ("POST", "/api/auth/login/email"),
        ("POST", "/api/auth/login/username"),
        ("POST", "/api/auth/register"),
        # Catálogo de inscripción (público por contrato).
        ("GET", "/api/catalogo/categorias"),
        ("GET", "/api/catalogo/disciplinas"),
        ("GET", "/api/catalogo/paquetes"),
        ("GET", "/api/catalogo/promociones"),
        # Cotización: pública y deliberadamente sin sesión.
        ("POST", "/api/cotizaciones"),
        # Edición vigente.
        ("GET", "/api/ediciones/actual"),
        # Tienda: catálogo y detalle son públicos.
        ("GET", "/api/marketplace/categorias"),
        ("GET", "/api/marketplace/productos"),
        ("GET", "/api/marketplace/productos/{slug}"),
        # Marketplace: el pedido se abre con su TOKEN, no con una sesión.
        ("GET", "/api/marketplace/pedidos/{token}"),
        # Pases: el lote se abre con su TOKEN, no con una sesión.
        ("GET", "/api/pases"),
        ("GET", "/api/pases/{pase_id}"),
        ("POST", "/api/pases/compras"),
        ("GET", "/api/pases/compras/{compra_pase_id}"),
        ("GET", "/api/pases/compras/{compra_pase_id}/beneficiarios"),
        ("POST", "/api/pases/compras/{compra_pase_id}/beneficiarios"),
        ("DELETE", "/api/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}"),
        # Búsqueda de personas por documento: pública por contrato.
        ("GET", "/api/personas/busqueda/{documento}"),
        # Notificación del proveedor: servidor a servidor, con firma propia.
        ("POST", "/api/pagos/izipay/notificacion"),
        # Tokens de `ninja_jwt` (controller de terceros).
        ("POST", "/api/token/pair"),
        ("POST", "/api/token/refresh"),
        ("POST", "/api/token/verify"),
    }
)

#: Superficies que exigen una CAPACIDAD del mapa central
#: (`core/capacidades.py`). Una cuenta del grupo `Normal` no tiene ninguna.
SUPERFICIES_CON_CAPACIDAD = (
    "/api/administracion/",
    "/api/competencias/",
    "/api/validaciones/",
)

#: Operaciones de escritura que exigen capacidad y NO viven bajo
#: `/api/administracion/**`.
ESCRITURAS_CON_CAPACIDAD = frozenset(
    {
        ("POST", "/api/marketplace/productos"),
        ("POST", "/api/patrocinadores"),
    }
)

#: Marcas que NUNCA pueden aparecer en el cuerpo de una denegación. Son las
#: huellas de una excepción no redactada, de una ruta interna o de una
#: consulta a la base de datos.
MARCAS_DE_FUGA = (
    "Traceback",
    "most recent call last",
    "site-packages",
    "django.",
    "psycopg",
    "OperationalError",
    "ProgrammingError",
    "IntegrityError",
    "SELECT ",
    "INSERT INTO",
    "UPDATE ",
    "Traceback (most recent",
    "File \"",
    "0x",
)


def _ruta_concreta(ruta: str) -> str:
    """Sustituye cada parámetro de la ruta por un identificador inexistente."""
    salida = ruta
    while "{" in salida:
        inicio = salida.index("{")
        fin = salida.index("}")
        salida = salida[:inicio] + ID_QUE_NO_EXISTE + salida[fin + 1 :]
    return salida


def _operaciones_vivas():
    """`(método, ruta)` de cada operación del registro vivo."""
    from config.api import api

    esquema = api.get_openapi_schema()
    operaciones = []

    for ruta, spec in esquema.get("paths", {}).items():
        for metodo in spec:
            if metodo.lower() in ("get", "post", "put", "patch", "delete"):
                operaciones.append((metodo.upper(), ruta))

    return sorted(operaciones)


def _protegidas():
    """Las operaciones que el esquema declara con `JWTAuth`."""
    from config.api import api

    esquema = api.get_openapi_schema()
    protegidas = []

    for ruta, spec in esquema.get("paths", {}).items():
        for metodo, detalle in spec.items():
            if metodo.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            seguridad = detalle.get("security")
            if seguridad:
                protegidas.append((metodo.upper(), ruta))

    return sorted(protegidas)


def _llamar(cliente, metodo, url, cabeceras=None):
    if metodo == "GET":
        return cliente.get(url, **(cabeceras or {}))
    return getattr(cliente, metodo.lower())(
        url,
        data=json.dumps({}),
        content_type="application/json",
        **(cabeceras or {}),
    )


def _cuerpo(respuesta) -> str:
    return respuesta.content.decode("utf-8", errors="replace")


# ── El registro vivo es el que se mide ───────────────────────────────────────


def test_el_registro_vivo_declara_al_menos_una_ruta_por_superficie():
    """La swept no puede pasar en vacío: se mide un registro real."""
    operaciones = _operaciones_vivas()

    assert len(operaciones) >= 70
    assert ("GET", "/api/administracion/resumen") in operaciones
    assert ("POST", "/api/inscripciones") in operaciones
    assert ("GET", "/api/marketplace/productos") in operaciones


def test_ninguna_operacion_nueva_se_vuelve_publica_sin_revision():
    """GIVEN el registro vivo · WHEN se compara con la lista congelada
    · THEN las operaciones públicas son EXACTAMENTE las declaradas.

    Una ruta nueva que se registre sin credencial rompe esta puerta: su
    dueño tiene que decidir, aquí, si es pública de verdad.
    """
    desde_el_registro = set(_operaciones_vivas()) - set(_protegidas())

    assert desde_el_registro == set(OPERACIONES_PUBLICAS_CONGELADAS), {
        "nuevas": sorted(desde_el_registro - set(OPERACIONES_PUBLICAS_CONGELADAS)),
        "ausentes": sorted(set(OPERACIONES_PUBLICAS_CONGELADAS) - desde_el_registro),
    }


# ── La frontera: anónimo NO entra ────────────────────────────────────────────


def test_ninguna_operacion_protegida_acepta_una_peticion_anonima():
    """GIVEN una petición sin cuenta · WHEN se recorre toda operación
    protegida · THEN TODAS responden 401 y ninguna devuelve 2xx ni 5xx."""
    protegidas = _protegidas()
    fallos = []

    assert len(protegidas) >= 50

    for metodo, ruta in protegidas:
        respuesta = _llamar(Client(), metodo, _ruta_concreta(ruta))

        if respuesta.status_code != 401:
            fallos.append(f"{metodo} {ruta} -> {respuesta.status_code}")

    assert not fallos, fallos


def test_la_denegacion_anonima_usa_el_codigo_congelado():
    """La denegación anónimo es `AUTHENTICATION_REQUIRED`, no un 403 ni un
    error del servidor: la autenticación se exige ANTES que el permiso."""
    from config.api import api

    esquema = api.get_openapi_schema()

    for ruta, spec in esquema.get("paths", {}).items():
        for metodo, detalle in spec.items():
            if metodo.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            if not detalle.get("security"):
                continue

            respuesta = _llamar(Client(), metodo.upper(), _ruta_concreta(ruta))
            cuerpo = respuesta.json()

            assert respuesta.status_code == 401, ruta
            assert cuerpo["success"] is False
            assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED", ruta
            assert cuerpo["data"] is None


def test_ninguna_denegacion_filtra_traza_ruta_ni_consulta():
    """El cuerpo de una denegación es la envoltura congelada con prosa
    pública: ni trazas, ni rutas internas, ni SQL, ni ids."""
    for metodo, ruta in _protegidas():
        respuesta = _llamar(Client(), metodo, _ruta_concreta(ruta))
        cuerpo = _cuerpo(respuesta)

        for marca in MARCAS_DE_FUGA:
            assert marca not in cuerpo, f"{metodo} {ruta} filtra {marca!r}"

        # La ruta interna del servidor tampoco.
        assert "/api/" not in cuerpo, f"{metodo} {ruta} filtra su propia ruta"
        # Y tampoco el identificador inexistente que se pidió.
        assert ID_QUE_NO_EXISTE not in cuerpo, f"{metodo} {ruta} filtra el id"


# ── La frontera: una cuenta normal NO administra ─────────────────────────────


@pytest.fixture
def usuario_normal(db):
    """Una cuenta del grupo funcional `Normal`: cero capacidades."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="ver02.normal",
        password="Prueba-12345",
    )


def test_una_cuenta_normal_no_alcanza_ninguna_superficie_con_capacidad(db, usuario_normal):
    """GIVEN una cuenta `Normal` · WHEN llama a una superficie que exige
    capacidad · THEN 403, nunca 2xx."""
    from ninja_jwt.tokens import AccessToken

    token = AccessToken.for_user(usuario_normal)
    cabeceras = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    fallos = []

    for metodo, ruta in _operaciones_vivas():
        exige = ruta.startswith(SUPERFICIES_CON_CAPACIDAD) or (
            metodo,
            ruta,
        ) in ESCRITURAS_CON_CAPACIDAD
        if not exige:
            continue

        respuesta = _llamar(Client(), metodo, _ruta_concreta(ruta), cabeceras)

        if respuesta.status_code != 403:
            fallos.append(f"{metodo} {ruta} -> {respuesta.status_code}")

    assert not fallos, fallos


def test_la_denegacion_por_capacidad_usa_el_codigo_congelado(db, usuario_normal):
    """403 es `ACTION_NOT_ALLOWED`: el catálogo público, no la excepción."""
    from ninja_jwt.tokens import AccessToken

    token = AccessToken.for_user(usuario_normal)
    respuesta = _llamar(
        Client(),
        "GET",
        "/api/administracion/resumen",
        {"HTTP_AUTHORIZATION": f"Bearer {token}"},
    )

    assert respuesta.status_code == 403
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "ACTION_NOT_ALLOWED"


# ── El alcance del token: un token ajeno no abre nada ───────────────────────


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("GET", "/api/pases/compras/{compra_pase_id}"),
        ("GET", "/api/pases/compras/{compra_pase_id}/beneficiarios"),
        ("POST", "/api/pases/compras/{compra_pase_id}/beneficiarios"),
        ("GET", "/api/marketplace/pedidos/{token}"),
    ],
)
def test_un_token_ajeno_no_abre_un_recurso_y_no_lo_revela(metodo, ruta):
    """GIVEN un token que no es de nadie · WHEN se usa · THEN 404.

    La respuesta NO dice "existe pero no es tuyo": dice lo mismo que si el
    recurso no existiera. Ésa es la denegación NEUTRA.
    """
    respuesta = _llamar(Client(), metodo, _ruta_concreta(ruta))

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] in {
        "COMPRA_PASE_NO_ENCONTRADA",
        "PEDIDO_NO_ENCONTRADO",
    }


def test_la_notificacion_del_proveedor_sin_firma_se_rechaza():
    """La única operación servidor-a-servidor NO acepta una notificación sin
    firma: su credencial es la firma, no una sesión."""
    respuesta = _llamar(Client(), "POST", "/api/pagos/izipay/notificacion")

    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "PAGO_NOTIFICACION_NO_VERIFICABLE"


# ── La denegación no confunde 404 con 403 ────────────────────────────────────


def test_la_denegacion_por_titularidad_es_la_congelada(
    db, usuario_normal, inscripcion
):
    """Un actor AUTENTICADO que no es el responsable recibe 403
    `INSCRIPCION_NO_AUTORIZADA`; un identificador que no existe recibe 404
    `INSCRIPCION_NO_ENCONTRADA`.

    Son DOS denegaciones distintas y ése es el comportamiento CONGELADO:
    `FR-03` §2.1 fija el código `INSCRIPCION_NO_AUTORIZADA` para "no es tuyo".
    La diferencia de código permite distinguir "existe" de "no existe": es un
    oráculo de existencia de BAJA severidad, heredado del contrato congelado
    (cambiarlo exige una enmienda de `FR-03`, fuera de las raíces de este
    packet). Se fija aquí para que sea un hecho declarado y no un accidente.
    """
    inexistente = str(uuid.uuid4())
    cabeceras = {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(usuario_normal)}"}

    respuesta_inexistente = _llamar(
        Client(), "GET", f"/api/inscripciones/{inexistente}", cabeceras
    )
    respuesta_ajena = _llamar(
        Client(),
        "GET",
        f"/api/inscripciones/{inscripcion.id}",
        cabeceras,
    )

    assert respuesta_inexistente.status_code == 404
    assert respuesta_inexistente.json()["error"]["code"] == "INSCRIPCION_NO_ENCONTRADA"

    assert respuesta_ajena.status_code == 403
    assert respuesta_ajena.json()["error"]["code"] == "INSCRIPCION_NO_AUTORIZADA"

    # Ninguna de las dos respuestas filtra datos del recurso.
    for respuesta in (respuesta_inexistente, respuesta_ajena):
        cuerpo = _cuerpo(respuesta)
        assert respuesta.json()["data"] is None
        assert str(inscripcion.id) not in cuerpo

