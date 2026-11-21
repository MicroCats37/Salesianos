"""Tests de la COMPRA PAGADA asistida: cotización, importe declarado y precio obsoleto.

Change: `administracion-pases-alta-directa`

GIVEN  un pase VIGENTE con su precio vigente y un administrador autenticado
WHEN   el administrador COTIZA el lote, lo COMPRA para un cliente y declara el
       importe que recibió
THEN   el precio unitario y el total los deriva el SERVIDOR (el navegador
       nunca calcula un importe), la cotización NO crea ningún hecho
       comercial, y el `monto_declarado` se guarda como EVIDENCIA AUDITADA
       sin mover el total canónico de la compra, el de la orden ni el estado
       del pago.

AND    el TOKEN DE PRECIO de la cotización detecta el precio obsoleto: si el
       catálogo se movió, el alta se rechaza con 409 `PRECIO_CAMBIADO` y NO
       se crea ni compra, ni orden, ni pago, ni identidad.

AND    la compra PÚBLICA y el MARKETPLACE quedan intactos (`R6`): no exponen
       el importe declarado y siguen congelando el precio de catálogo.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §8 — tests de integración
contra la base real, con `django.test.Client` (los controllers son async).
"""

import json
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.administracion.tests.fixtures.asistido_fixtures import (  # noqa: F401
    admin_con_persona,
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


def _cotizar(cliente, cabeceras, pase_id, cantidad):
    """La cotización del servidor, tal como la ve el administrador."""
    respuesta = _post(
        cliente,
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(pase_id), "cantidad": cantidad},
        cabeceras,
    )
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()["data"]


def _comprar(cliente, cabeceras, pase_id, cantidad, evidencia, documento="77777777"):
    """La compra asistida de un lote de pases para un cliente."""
    return _post(
        cliente,
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_id),
            "cantidad": cantidad,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": documento,
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": evidencia,
        },
        cabeceras,
    )


def _mover_el_precio(pase, monto="40.00"):
    """MUEVE el precio del catálogo: una ventana nueva que hoy rigió.

    La fila nueva arranca HOY, así que gana sobre la anterior (el selector
    toma la de `vigente_desde` más reciente). El token de precio cambia.
    """
    from modules.salesianos_fest.domain.models import PasePrecio

    return PasePrecio.objects.create(
        pase=pase,
        monto=Decimal(monto),
        moneda="PEN",
        vigente_desde=date.today(),
    )


def _hechos_comerciales():
    """El CONTABLE de los hechos comerciales: compra, lote, orden y evidencia."""
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase

    return {
        "compras": Compra.objects.count(),
        "lotes": CompraPase.objects.count(),
        "ordenes": OrdenPago.objects.count(),
        "aprobaciones": AprobacionPagoManual.objects.count(),
    }


# ── La cotización: el servidor calcula, el navegador no ─────────────────────


def test_la_cotizacion_publica_el_precio_y_el_total_del_servidor(
    pase_venta, admin_con_persona
):
    """GIVEN un pase VIGENTE con precio vigente · WHEN el administrador
    COTIZA tres pases · THEN el precio unitario, el total, la moneda y el
    token de precio los publica el SERVIDOR.

    El total NO lo calcula el navegador: viaja como TEXTO con dos decimales,
    y el token identifica la fila de precio exacta que rigió."""
    respuesta = _post(
        Client(),
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(pase_venta.id), "cantidad": 3},
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["message"] == "Cotización calculada correctamente."

    datos = cuerpo["data"]
    assert datos["pase_id"] == str(pase_venta.id)
    assert datos["pase_nombre"] == "Pase FEST"
    assert datos["cantidad"] == 3
    assert datos["precio_unitario"] == "35.00"
    assert datos["total"] == "105.00"
    assert datos["moneda"] == "PEN"
    assert datos["estado"] == "ACTIVA"
    # El token de concurrencia es un identificador estable y corto.
    assert len(datos["version"]) == 16
    assert datos["version"].isalnum()
    assert datos["validez_hasta"]


def test_la_cotizacion_no_crea_compra_ni_pago(pase_venta, admin_con_persona):
    """GIVEN un pase a la venta · WHEN el administrador COTIZA · THEN NO se
    crea ni una compra, ni un lote, ni una orden de pago, ni una evidencia,
    ni un acta: la cotización es una LECTURA."""
    from modules.administracion.domain.models import AccionAuditada

    antes = _hechos_comerciales()
    actas_antes = AccionAuditada.objects.count()

    _cotizar(Client(), _cabeceras(admin_con_persona), pase_venta.id, 2)

    assert _hechos_comerciales() == antes
    assert AccionAuditada.objects.count() == actas_antes


def test_la_cotizacion_exige_la_cantidad_del_dominio(pase_venta, admin_con_persona):
    """GIVEN una cantidad FUERA de los límites del dominio · WHEN se cotiza ·
    THEN 422 `CANTIDAD_INVALIDA`: el dueño del pase acota el lote."""
    respuesta = _post(
        Client(),
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(pase_venta.id), "cantidad": 51},
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422, respuesta.content
    assert _codigo_de_error(respuesta) == "CANTIDAD_INVALIDA"


def test_la_cotizacion_de_un_pase_inexistente_es_404(
    edicion_con_tienda_y_pases, admin_con_persona
):
    """GIVEN un pase que NO existe · WHEN se cotiza · THEN 404
    `PASE_NO_ENCONTRADO`: la cotización no inventa un precio de reserva."""
    from uuid import uuid4

    respuesta = _post(
        Client(),
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(uuid4()), "cantidad": 1},
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 404, respuesta.content
    assert _codigo_de_error(respuesta) == "PASE_NO_ENCONTRADO"


def test_la_cotizacion_exige_cuenta_y_permiso(usuario_responsable, pase_venta):
    """GIVEN una petición SIN cuenta y una cuenta SIN capacidades · WHEN se
    cotiza · THEN 401 y 403: el permiso se comprueba ANTES que el catálogo."""
    anonima = _post(
        Client(),
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(pase_venta.id), "cantidad": 1},
        {},
    )
    assert anonima.status_code == 401, anonima.content
    assert _codigo_de_error(anonima) == "AUTHENTICATION_REQUIRED"

    sin_permiso = _post(
        Client(),
        "/api/administracion/pases/cotizacion",
        {"pase_id": str(pase_venta.id), "cantidad": 1},
        _cabeceras(usuario_responsable),
    )
    assert sin_permiso.status_code == 403, sin_permiso.content
    assert _codigo_de_error(sin_permiso) == "ACTION_NOT_ALLOWED"


# ── El importe declarado: evidencia auditada, no verdad financiera ──────────


def test_el_monto_declarado_se_guarda_y_no_altera_el_total_canonico(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN un pase de S/ 35.00 · WHEN el administrador compra DOS pases y
    DECLARA haber recibido S/ 30.00 · THEN el importe declarado se guarda
    junto a la evidencia y el TOTAL canónico sigue siendo el de catálogo
    (S/ 70.00) en la compra, en el lote, en la orden y en la evidencia.

    El importe declarado es INFORMATIVO: no es el precio, no es el total y no
    mueve el estado del pago ni el de la compra."""
    from modules.commerce.domain.constants import EstadoCompra
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.constants import EstadoOrdenPago
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        2,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-DECL-0001",
            "motivo": "Cobro en la boletería del FEST.",
            "monto_declarado": "30.00",
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["monto_declarado"] == "30.00"
    assert cuerpo["total"] == "70.00"

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    compra = Compra.objects.get(id=lote.compra_id)
    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)

    # El importe DECLARADO es evidencia auditada.
    assert aprobacion.monto_declarado == Decimal("30.00")
    # El total CANÓNICO no se tocó: es el del catálogo (35.00 x 2).
    assert aprobacion.monto == Decimal("70.00")
    assert aprobacion.moneda == "PEN"
    assert orden.monto == Decimal("70.00")
    assert compra.total == Decimal("70.00")
    assert lote.total == Decimal("70.00")
    assert lote.precio_unitario == Decimal("35.00")
    # Y el snapshot de la línea sigue con el precio de catálogo.
    linea = compra.lineas_snapshot[0]
    assert linea["cantidad"] == 2
    assert float(linea["precio_aplicado"]) == 35.0

    # Los ESTADOS tampoco se mueven: el pago está liquidado y la compra pagada.
    assert orden.estado == EstadoOrdenPago.CONFIRMADA
    assert compra.estado == EstadoCompra.PAGADA


def test_el_monto_declarado_igual_al_total_no_cambia_nada(
    pase_venta, admin_con_persona
):
    """GIVEN un pase de S/ 35.00 · WHEN el administrador declara S/ 70.00 por
    DOS pases · THEN el importe declarado coincide con el total y nada se
    mueve: el total canónico sigue siendo S/ 70.00."""
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago

    respuesta = _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        2,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-DECL-0002",
            "motivo": "Cobro en la boletería del FEST.",
            "monto_declarado": "70.00",
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["monto_declarado"] == "70.00"
    assert cuerpo["total"] == "70.00"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.monto_declarado == Decimal("70.00")
    assert aprobacion.monto == Decimal("70.00")
    assert orden.monto == Decimal("70.00")


def test_el_monto_declarado_cero_es_valido_y_no_altera_el_total(
    pase_venta, admin_con_persona
):
    """GIVEN un pase de S/ 35.00 · WHEN el administrador declara S/ 0 (no
    cobró) · THEN el importe declarado se guarda como cero y el total
    canónico sigue siendo S/ 35.00: declararlo NO convierte la compra en
    una cortesía ni inventa un hecho financiero."""
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago

    respuesta = _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        1,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-DECL-0003",
            "motivo": "Cobro en la boletería del FEST.",
            "monto_declarado": "0",
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["monto_declarado"] == "0.00"
    assert cuerpo["total"] == "35.00"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.monto_declarado == Decimal("0.00")
    assert aprobacion.monto == Decimal("35.00")
    assert orden.monto == Decimal("35.00")


def test_el_monto_declarado_mayor_que_el_total_se_guarda_sin_mover_el_total(
    pase_venta, admin_con_persona
):
    """GIVEN un pase de S/ 35.00 · WHEN el administrador declara S/ 100.00 ·
    THEN el importe declarado se guarda tal cual y el total canónico sigue
    siendo S/ 35.00: el declarado es EVIDENCIA, no una orden de cobro."""
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago

    respuesta = _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        1,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-DECL-0004",
            "motivo": "Cobro en la boletería del FEST.",
            "monto_declarado": "100.00",
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["monto_declarado"] == "100.00"
    assert cuerpo["total"] == "35.00"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.monto_declarado == Decimal("100.00")
    assert aprobacion.monto == Decimal("35.00")
    assert orden.monto == Decimal("35.00")


def test_el_monto_declarado_ausente_queda_sin_declarar(pase_venta, admin_con_persona):
    """GIVEN una compra SIN importe declarado · WHEN se registra · THEN la
    evidencia queda con el importe declarado VACÍO ("no declarado") y el
    total canónico es el de catálogo."""
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago

    respuesta = _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        1,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-DECL-0005",
            "motivo": "Cobro en la boletería del FEST.",
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["monto_declarado"] is None
    assert cuerpo["total"] == "35.00"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.monto_declarado is None
    assert aprobacion.monto == Decimal("35.00")


def test_el_acta_audita_el_importe_declarado(pase_venta, admin_con_persona):
    """GIVEN una compra con importe declarado · WHEN se revisa el ACTA · THEN
    el acta nombra el importe declarado Y el total canónico: la auditoría
    dice lo que pasó, sin convertir el declarado en el total."""
    from modules.administracion.domain.models import AccionAuditada

    _comprar(
        Client(),
        _cabeceras(admin_con_persona),
        pase_venta.id,
        2,
        {
            "canal": "YAPE",
            "referencia": "OP-DECL-0001",
            "motivo": "Pago por Yape registrado en la mesa.",
            "monto_declarado": "30.00",
        },
    )

    acta = AccionAuditada.objects.get(accion="COMPRAR_PASE_PARA_CLIENTE")
    assert acta.actor_usuario_id == admin_con_persona.id
    assert acta.datos["monto_declarado"] == "30.00"
    assert acta.datos["total"] == "70.00"
    assert acta.datos["moneda"] == "PEN"
    assert acta.datos["cantidad"] == 2


# ── El precio obsoleto: 409 y ningún hecho comercial ────────────────────────


def test_la_compra_con_el_precio_obsoleto_se_rechaza_y_no_crea_nada(
    pase_venta, admin_con_persona
):
    """GIVEN una cotización de S/ 35.00 · WHEN el catálogo SUBE a S/ 40.00 y
    el administrador envía el alta con el token viejo · THEN 409
    `PRECIO_CAMBIADO` y NO se crea ni compra, ni lote, ni orden, ni evidencia,
    ni acta, ni la identidad del cliente.

    El precio se comprueba ANTES de tocar nada: nadie cobra una cantidad que
    no vio."""
    from modules.administracion.domain.models import AccionAuditada
    from modules.usuarios.domain.models import Persona

    cliente = Client()
    cabeceras = _cabeceras(admin_con_persona)

    cotizacion = _cotizar(cliente, cabeceras, pase_venta.id, 2)
    _mover_el_precio(pase_venta, "40.00")

    antes = _hechos_comerciales()
    actas_antes = AccionAuditada.objects.count()
    personas_antes = Persona.objects.count()

    respuesta = _comprar(
        cliente,
        cabeceras,
        pase_venta.id,
        2,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-OBS-0001",
            "motivo": "Cobro en la boletería del FEST.",
            "precio_version": cotizacion["version"],
        },
        documento="66666699",
    )

    assert respuesta.status_code == 409, respuesta.content
    assert _codigo_de_error(respuesta) == "PRECIO_CAMBIADO"

    assert _hechos_comerciales() == antes
    assert AccionAuditada.objects.count() == actas_antes
    assert Persona.objects.count() == personas_antes
    assert not Persona.objects.filter(numero_documento="66666699").exists()


def test_la_compra_con_el_token_de_la_cotizacion_se_acepta(
    pase_venta, admin_con_persona
):
    """GIVEN una cotización vigente · WHEN el administrador envía el alta con
    su token de precio · THEN 201 y el total es EXACTAMENTE el cotizado: la
    cotización y la compra dicen lo mismo."""
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraPase

    cliente = Client()
    cabeceras = _cabeceras(admin_con_persona)

    cotizacion = _cotizar(cliente, cabeceras, pase_venta.id, 2)

    respuesta = _comprar(
        cliente,
        cabeceras,
        pase_venta.id,
        2,
        {
            "canal": "EFECTIVO",
            "referencia": "REC-TOKEN-0001",
            "motivo": "Cobro en la boletería del FEST.",
            "precio_version": cotizacion["version"],
        },
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["total"] == cotizacion["total"]

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    compra = Compra.objects.get(id=lote.compra_id)
    assert compra.total == Decimal(cotizacion["total"])


# ── La frontera congelada: la compra pública y el Marketplace no cambian ─────


def test_la_compra_publica_de_pases_no_cambia_de_contrato(
    pase_venta, cliente_externo
):
    """GIVEN un visitante SIN cuenta · WHEN compra pases por la ruta PÚBLICA ·
    THEN 201, el lote queda PENDIENTE con el total de catálogo y NO existe
    ninguna evidencia manual: la compra pública no conoce el importe
    declarado (`R6`)."""
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import AprobacionPagoManual
    from modules.salesianos_fest.domain.constants import EstadoCompraPase
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _post(
        Client(),
        "/api/pases/compras",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 2,
            "tipo_documento": "DNI",
            "numero_documento": "90909090",
            "nombres": "Visitante",
            "apellidos": "Invitado",
            "contacto_email": "visitante@example.com",
        },
        {},
    )

    assert respuesta.status_code == 201, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["estado"] == EstadoCompraPase.PENDIENTE
    assert float(datos["total"]) == 70.0

    lote = CompraPase.objects.get(id=datos["compra_pase_id"])
    compra = Compra.objects.get(id=lote.compra_id)
    assert compra.total == Decimal("70.00")
    # La ruta pública NO aprueba el pago: no hay evidencia manual.
    assert not AprobacionPagoManual.objects.exists()


def test_el_marketplace_asistido_no_expone_el_importe_declarado(
    producto_tienda, admin_con_persona
):
    """GIVEN la compra asistida de TIENDA · WHEN se envía con un importe
    declarado en la evidencia · THEN el Marketplace lo IGNORA: su contrato
    HTTP no expone ese campo, la respuesta lo echoes como `null` y la
    evidencia queda sin importe declarado (`R6`)."""
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago

    respuesta = _post(
        Client(),
        "/api/administracion/marketplace/pedidos-cliente",
        {
            "items": [
                {
                    "tipo": "PRODUCTO",
                    "producto_id": str(producto_tienda.id),
                    "cantidad": 2,
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
                "canal": "TRANSFERENCIA_BANCARIA",
                "referencia": "OP-MKT-0001",
                "motivo": "Transferencia recibida por el banco del FEST.",
                "monto_declarado": "1.00",
                "precio_version": "version-inventada",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["tipo"] == "PEDIDO"
    assert cuerpo["monto_declarado"] is None

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.monto_declarado is None
    assert aprobacion.monto == orden.monto
