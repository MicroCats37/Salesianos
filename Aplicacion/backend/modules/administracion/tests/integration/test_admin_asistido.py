"""Tests de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

GIVEN  un equipo con su plantilla y un administrador autenticado
WHEN   el administrador agrega un participante por documento o compra para un
       cliente externo
THEN   el comando usa las REGLAS del dueño (capacidad, duplicado,
       disciplina, elegibilidad), el COMPRADOR es el CLIENTE y nunca el
       administrador, el pago queda liquidado por el flujo canónico del
       dueño y la acción queda en el ACTA con QUIÉN, QUÉ y POR QUÉ.

AND    el alta de un participante NO crea una persona y la retirada NO borra
       una `Persona`: el padrón es intocable desde aquí.
"""

import json

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.administracion.tests.fixtures.asistido_fixtures import (  # noqa: F401
    admin_con_persona,
    admin_sin_persona,
    categoria_tienda,
    cliente_externo,
    edicion_con_tienda_y_pases,
    pase_venta,
    producto_tienda,
)

pytestmark = pytest.mark.django_db


# ── Utilidades ──────────────────────────────────────────────────────────────


def _cabeceras(usuario):
    """Las cabeceras de una petición autenticada como `usuario`."""
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(usuario)}"}


def _post(cliente, url, cuerpo, cabeceras):
    """Una petición JSON."""
    return cliente.post(
        url,
        data=json.dumps(cuerpo),
        content_type="application/json",
        **cabeceras,
    )


def _codigo_de_error(respuesta):
    """El código estable del error de la envoltura congelada."""
    return respuesta.json()["error"]["code"]


# ── La plantilla del equipo ─────────────────────────────────────────────────


def test_el_alta_por_documento_agrega_a_la_plantilla(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN una persona EXISTENTE en el padrón · WHEN el administrador la
    agrega al equipo por su documento · THEN la participación existe y el
    ACTA nombra al administrador, el motivo y la acción."""
    from modules.administracion.domain.models import AccionAuditada
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(persona_participante.id)
    assert cuerpo["rol"] == "JUGADOR"
    assert cuerpo["estado"] == "ACTIVA"

    participacion = Participacion.objects.get(id=cuerpo["participacion_id"])
    assert participacion.equipo_id == equipo.id
    assert participacion.inscripcion_id == equipo.inscripcion_id

    acta = AccionAuditada.objects.get(accion="AGREGAR_PARTICIPANTE_EQUIPO")
    assert acta.actor_usuario_id == admin_con_persona.id
    assert acta.motivo == "Inscripción presencial en la mesa de control."


def test_el_alta_no_crea_una_persona(equipo, admin_con_persona):
    """GIVEN un documento que NO está en el padrón · WHEN el administrador
    intenta agregar a esa persona · THEN 404 y NO se crea ninguna `Persona`.

    La UI administrativa no expone un CRUD de `Persona`: agregar un
    participante no puede inventar una identidad."""
    from modules.usuarios.domain.models import Persona

    antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "rol": "JUGADOR",
            "motivo": "Intento de alta de un documento inexistente.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 404
    assert _codigo_de_error(respuesta) == "PERSONA_NO_ENCONTRADA"
    assert Persona.objects.count() == antes


def test_el_alta_exige_el_motivo(equipo, persona_participante, admin_con_persona):
    """GIVEN un comando sin motivo · WHEN se envía · THEN 422
    `MOTIVO_REQUERIDO`: sin motivo no hay acta y sin acta no hay comando."""
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "   ",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "MOTIVO_REQUERIDO"
    assert not Participacion.objects.exists()


def test_el_alta_respeta_el_duplicado_del_dueno(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN una persona YA en la plantilla · WHEN se la agrega otra vez ·
    THEN el DUEÑO lo rechaza con su propio código: este comando no
    reimplementa la regla de duplicado."""
    from modules.salesianos_fest.domain.models import Participacion

    primero = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Alta de la primera vez.",
        },
        _cabeceras(admin_con_persona),
    )
    assert primero.status_code == 201

    segundo = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Alta repetida.",
        },
        _cabeceras(admin_con_persona),
    )

    assert segundo.status_code == 422
    assert _codigo_de_error(segundo) == "PARTICIPANTE_DUPLICADO"
    assert Participacion.objects.count() == 1


# ── La compra asistida de pases ─────────────────────────────────────────────


def test_la_compra_de_pases_tiene_al_cliente_como_comprador(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN un cliente de tercera persona · WHEN el administrador compra
    pases para él · THEN el COMPRADOR es el cliente y NUNCA el
    administrador, aunque el administrador tenga persona vinculada."""
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 2,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0001",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["tipo"] == "PASE"
    assert cuerpo["comprador_persona_id"] == str(cliente_externo.id)
    assert cuerpo["comprador_persona_id"] != str(admin_con_persona.persona_fk_id)
    assert cuerpo["cantidad"] == 2

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    assert str(lote.comprador_id) == str(cliente_externo.id)

    compra = Compra.objects.get(id=lote.compra_id)
    assert str(compra.persona_id) == str(cliente_externo.id)
    assert str(compra.id) == cuerpo["compra_id"]


def test_la_compra_de_pases_liquida_el_pago_con_el_flujo_canonico(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN una compra asistida · WHEN el administrador registra la
    evidencia del pago · THEN la orden queda CONFIRMADA, la EVIDENCIA
    MANUAL queda persistida y la compra consta pagada."""
    from modules.commerce.domain.constants import EstadoCompra
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.constants import EstadoOrdenPago
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0002",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    assert orden.estado == EstadoOrdenPago.CONFIRMADA

    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.canal == "EFECTIVO"
    assert aprobacion.referencia == "REC-0002"
    assert str(aprobacion.actor_id) == str(admin_con_persona.id)

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    compra = Compra.objects.get(id=lote.compra_id)
    assert compra.estado == EstadoCompra.PAGADA


def test_la_compra_de_pases_deja_el_acta_con_el_administrador(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN una compra asistida · WHEN se revisa el ACTA · THEN nombra al
    ADMINISTRADOR como actor y guarda el motivo y la referencia."""
    from modules.administracion.domain.models import AccionAuditada

    _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "YAPE",
                "referencia": "OP-9988",
                "motivo": "Pago por Yape registrado en la mesa.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    acta = AccionAuditada.objects.get(accion="COMPRAR_PASE_PARA_CLIENTE")
    assert acta.actor_usuario_id == admin_con_persona.id
    assert acta.motivo == "Pago por Yape registrado en la mesa."
    assert acta.datos["referencia"] == "OP-9988"
    assert acta.datos["canal"] == "YAPE"


# ── La compra asistida de tienda ────────────────────────────────────────────


def test_el_pedido_de_tienda_tiene_al_cliente_como_comprador(
    producto_tienda, cliente_externo, admin_con_persona
):
    """GIVEN un cliente de tercera persona · WHEN el administrador pide la
    tienda para él · THEN el PEDIDO y su COMPRA son del cliente, el stock
    queda reservado y el pago queda liquidado."""
    from modules.commerce.domain.constants import EstadoCompra
    from modules.commerce.domain.models import Compra
    from modules.marketplace.domain.models import Pedido
    from modules.pagos.domain.constants import EstadoOrdenPago
    from modules.pagos.domain.models import OrdenPago

    respuesta = _post(
        Client(),
        "/api/administracion/marketplace/pedidos-cliente",
        {
            "items": [
                {"tipo": "PRODUCTO", "producto_id": str(producto_tienda.id), "cantidad": 2}
            ],
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "TRANSFERENCIA_BANCARIA",
                "referencia": "OP-7788",
                "motivo": "Transferencia recibida por el banco del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["tipo"] == "PEDIDO"
    assert cuerpo["comprador_persona_id"] == str(cliente_externo.id)
    assert cuerpo["comprador_persona_id"] != str(admin_con_persona.persona_fk_id)
    assert cuerpo["cantidad"] == 2

    pedido = Pedido.objects.get(id=cuerpo["recurso_id"])
    assert str(pedido.comprador_id) == str(cliente_externo.id)
    assert pedido.contacto_email == "rosa@example.com"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    assert orden.estado == EstadoOrdenPago.CONFIRMADA

    compra = Compra.objects.get(id=pedido.compra_id)
    assert str(compra.persona_id) == str(cliente_externo.id)
    assert str(compra.id) == cuerpo["compra_id"]
    assert compra.estado == EstadoCompra.PAGADA


def test_el_cliente_inexistente_se_registra_en_el_padron(
    pase_venta, admin_con_persona
):
    """GIVEN un cliente que NO está en el padrón · WHEN se compra para él ·
    THEN su identidad civil se REGISTRA y es la compradora: el cliente no
    necesita cuenta."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "66666666",
                "nombres": "Elena",
                "apellidos": "Vega",
                "contacto_email": "elena@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0003",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]

    persona = Persona.objects.get(numero_documento="66666666")
    assert persona.nombres == "Elena"
    assert cuerpo["comprador_persona_id"] == str(persona.id)


# ── La frontera de permisos ─────────────────────────────────────────────────


def test_una_cuenta_normal_no_alcanza_los_comandos_asistidos(
    usuario_responsable, equipo, persona_participante, pase_venta, producto_tienda
):
    """GIVEN una cuenta sin capacidades · WHEN llama a los tres comandos ·
    THEN 403 `ACTION_NOT_ALLOWED`: el permiso se comprueba ANTES que la
    forma del cuerpo."""
    cabeceras = _cabeceras(usuario_responsable)
    cliente = Client()

    respuestas = [
        _post(
            cliente,
            f"/api/administracion/equipos/{equipo.id}/participantes",
            {
                "tipo_documento": "DNI",
                "numero_documento": "33333333",
                "rol": "JUGADOR",
                "motivo": "Intento sin capacidades.",
            },
            cabeceras,
        ),
        _post(
            cliente,
            "/api/administracion/pases/compras-cliente",
            {
                "pase_id": str(pase_venta.id),
                "cantidad": 1,
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0004",
                    "motivo": "Intento sin capacidades.",
                },
            },
            cabeceras,
        ),
        _post(
            cliente,
            "/api/administracion/marketplace/pedidos-cliente",
            {
                "items": [
                    {
                        "tipo": "PRODUCTO",
                        "producto_id": str(producto_tienda.id),
                        "cantidad": 1,
                    }
                ],
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0005",
                    "motivo": "Intento sin capacidades.",
                },
            },
            cabeceras,
        ),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 403, respuesta.content
        assert _codigo_de_error(respuesta) == "ACTION_NOT_ALLOWED"


def test_una_peticion_anonima_no_alcanza_los_comandos_asistidos(
    equipo, pase_venta, producto_tienda
):
    """GIVEN una petición SIN cuenta · WHEN llama a los tres comandos · THEN
    401 `AUTHENTICATION_REQUIRED`: la autenticación se exige ANTES que el
    permiso."""
    cliente = Client()

    respuestas = [
        _post(
            cliente,
            f"/api/administracion/equipos/{equipo.id}/participantes",
            {
                "tipo_documento": "DNI",
                "numero_documento": "33333333",
                "rol": "JUGADOR",
                "motivo": "Intento anónimo.",
            },
            {},
        ),
        _post(
            cliente,
            "/api/administracion/pases/compras-cliente",
            {
                "pase_id": str(pase_venta.id),
                "cantidad": 1,
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0006",
                    "motivo": "Intento anónimo.",
                },
            },
            {},
        ),
        _post(
            cliente,
            "/api/administracion/marketplace/pedidos-cliente",
            {
                "items": [
                    {
                        "tipo": "PRODUCTO",
                        "producto_id": str(producto_tienda.id),
                        "cantidad": 1,
                    }
                ],
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0007",
                    "motivo": "Intento anónimo.",
                },
            },
            {},
        ),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401, respuesta.content
        assert _codigo_de_error(respuesta) == "AUTHENTICATION_REQUIRED"
