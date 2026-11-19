"""Fixtures y helpers de prueba del módulo `pagos`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Los helpers de este archivo son **funciones puras** que construyen el mundo de
la prueba: una persona, una orden, un intento, un payload de proveedor y su
firma. No hay mocks que puedan convertirse en un camino de producción: la
firma se calcula de verdad con HMAC-SHA256 sobre el payload crudo, igual que
la verificación real.
"""

import base64
import hashlib
import hmac
import json
from decimal import Decimal

import pytest

from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import EstadoOrdenPago, EstadoTransaccionPago
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.usuarios.domain.models import Persona, Usuario

#: Clave de comercio de PRUEBA. No es un secreto: es una constante del test
#: y sólo existe dentro del proceso de prueba.
CLAVE_COMERCIO_PRUEBA = "clave-de-comercio-de-prueba-no-secreta"


# ── Personas y cuentas ──────────────────────────────────────────────────────


@pytest.fixture
def persona(db):
    """La persona compradora."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="11111111",
    )


@pytest.fixture
def otra_persona(db):
    """Una persona que NO es la compradora de las órdenes de la prueba."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
    )


@pytest.fixture
def usuario_comprador(persona):
    """Una cuenta con sesión y persona: el actor de las rutas privadas."""
    return Usuario.objects.create_user(
        username="comprador",
        password="clave-de-prueba",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_ajeno(otra_persona):
    """Una cuenta con sesión de OTRA persona."""
    return Usuario.objects.create_user(
        username="ajeno",
        password="clave-de-prueba",
        persona_fk=otra_persona,
    )


# ── Comercio y pagos ────────────────────────────────────────────────────────


@pytest.fixture
def orden_pago(db):
    """Una orden de pago `PENDIENTE` de 100.00 PEN."""
    return OrdenPago.objects.create(
        referencia="ORD-PRUEBA-0001",
        estado=EstadoOrdenPago.PENDIENTE,
        monto=Decimal("100.00"),
        moneda="PEN",
    )


@pytest.fixture
def compra(persona, orden_pago):
    """La compra que financia la orden de pago de la prueba."""
    return Compra.objects.create(
        persona=persona,
        origen=OrigenCompra.INSCRIPCION,
        estado=EstadoCompra.PENDIENTE,
        total=Decimal("100.00"),
        moneda="PEN",
        lineas_snapshot=[
            {
                "concepto_tipo": "PAQUETE",
                "concepto_id": "paquete-1",
                "concepto_nombre": "Paquetecompetitive",
                "cantidad": 1,
                "precio_unitario": "100.00",
                "precio_aplicado": "100.00",
            }
        ],
        referencia="INSCRIPCION:1:INICIAL",
        orden_pago=orden_pago,
    )


@pytest.fixture
def intento(orden_pago):
    """El intento `PENDIENTE` de la orden de la prueba."""
    return TransaccionPago.objects.create(
        orden_pago=orden_pago,
        intento=1,
        referencia_proveedor="10000000000001",
        estado=EstadoTransaccionPago.PENDIENTE,
    )


# ── Entorno ─────────────────────────────────────────────────────────────────


@pytest.fixture
def clave_comercio(settings):
    """Configura una clave de comercio de prueba.

    La clave real NUNCA se usa en los tests: es una constante pública del
    archivo, no un secreto de despliegue.
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO_PRUEBA
    return CLAVE_COMERCIO_PRUEBA


@pytest.fixture
def sin_clave_comercio(settings):
    """Deja el entorno SIN clave del comercio: la verificación no está disponible."""
    settings.IZIPAY_KEY_HASH = ""


@pytest.fixture(scope="session")
def injector():
    """El inyector de dependencias del paquete FND-04.

    Reúne los módulos de DI de `commerce` y `pagos` para que los flujos se
    construyan con sus puertos reales (no con dobles).
    """
    from injector import Injector

    from modules.commerce.di import CommerceModule
    from modules.pagos.di import PagosModule

    return Injector([CommerceModule, PagosModule])


# ── Helpers de payload y firma ──────────────────────────────────────────────


def payload_confirmacion(
    *,
    transaction_id: str,
    codigo: str = "00",
    monto: str = "100.00",
    moneda: str = "PEN",
    order_number: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Construye el payload de confirmación que entrega el proveedor."""
    payload = {
        "code": codigo,
        "message": "Operación finalizada",
        "transactionId": transaction_id,
        "amount": monto,
        "currency": moneda,
        "response": {"payMethod": "Visa"},
    }
    if order_number:
        payload["orderNumber"] = order_number
    if extra:
        payload.update(extra)
    return payload


def payload_http(payload: dict) -> str:
    """Serializa el payload como el texto crudo que firma el proveedor."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def firmar(payload_crudo: str, clave: str = CLAVE_COMERCIO_PRUEBA) -> str:
    """Firma el payload crudo con HMAC-SHA256 en Base64.

    Es la misma operación que hace la verificación real: si el test pasa, la
    firma del servidor también verifica.
    """
    resumen = hmac.new(
        clave.encode("utf-8"),
        payload_crudo.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(resumen).decode("ascii")


__all__ = [
    "CLAVE_COMERCIO_PRUEBA",
    "firmar",
    "payload_confirmacion",
    "payload_http",
]
