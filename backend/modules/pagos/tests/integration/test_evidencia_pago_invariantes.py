"""
Cross-product invariants of the payment evidence of an order.

The payment evidence is the TRUTH of a payment: an order is paid ONLY when it
carries a CORRELATED successful provider transaction OR an active manual
approval. The administrative projection derives the origin from that SAME
predicate, so the two can never disagree.

This module walks the CROSS PRODUCT of the three axes that describe an order
and asserts that they never contradict each other:

- the STATE of the order (PENDIENTE / PAGADA / CANCELADA),
- the EVIDENCE it carries (nothing, an open attempt, a failed attempt, a
  correlated success, a success with a mismatched amount or currency, an
  active or an annulled manual approval),
- the PAYMENT DATE (`pagada_en`), which exists EXACTLY for a paid order.

Three invariants hold for EVERY combination: a PAID order always carries
verifiable evidence, the payment date exists if and only if the order is paid,
and the derived origin is a function of the EVIDENCE — never of the state:
the bulk projection and the per-order predicate always agree.
"""
import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.pagos.domain.constants import (
    CanalPagoManual,
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrigenPago,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import (
    AprobacionPagoManual,
    OrdenPago,
    TransaccionPago,
)
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.usuarios.domain.models.persona import Persona

PENDIENTE = OrdenPagoStatus.PENDIENTE
PAGADA = OrdenPagoStatus.PAGADA
CANCELADA = OrdenPagoStatus.CANCELADA
SIN_PAGO = OrigenPago.SIN_PAGO
IZIPAY = OrigenPago.IZIPAY
MANUAL = OrigenPago.MANUAL

# ── The cross product ─────────────────────────────────────────────────────────
#
# (nombre, estado de la orden, evidencia, origen esperado, tiene evidencia,
#  esta pagada)

CASOS = [
    ("sin_evidencia_pendiente", PENDIENTE, "ninguna", SIN_PAGO, False, False),
    ("sin_evidencia_cancelada", CANCELADA, "ninguna", SIN_PAGO, False, False),
    ("intento_abierto", PENDIENTE, "intento", SIN_PAGO, False, False),
    ("intento_fallido", PENDIENTE, "fallido", SIN_PAGO, False, False),
    ("exito_correlacionado", PAGADA, "exito", IZIPAY, True, True),
    ("exito_con_monto_distinto", PENDIENTE, "exito_monto", SIN_PAGO, False, False),
    ("exito_con_moneda_distinta", PENDIENTE, "exito_moneda", SIN_PAGO, False, False),
    ("aprobacion_activa", PAGADA, "manual_activa", MANUAL, True, True),
    ("aprobacion_anulada", CANCELADA, "manual_anulada", SIN_PAGO, False, False),
    ("aprobacion_activa_sin_cobrar", PENDIENTE, "manual_activa", MANUAL, True, False),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _crear_usuario():
    """Create the account that signs a manual approval."""
    User = get_user_model()
    marca = uuid.uuid4().hex[:8]
    persona = Persona.objects.create(
        nombres="Actor",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="M",
    )
    return User.objects.create_user(
        username=f"actor_{marca}",
        email=f"actor_{marca}@example.com",
        password="testpass123",
        persona_fk=persona,
    )


def _crear_orden(estado: str, clave: str) -> OrdenPago:
    """Create an order in the given state, with its payment date when paid."""
    return OrdenPago.objects.create(
        numero=f"ORD-{clave[:8].upper()}-{uuid.uuid4().hex[:6].upper()}",
        monto_total=Decimal("100.00"),
        moneda="PEN",
        estado=estado,
        pagada_en=timezone.now() if estado == PAGADA else None,
    )


def _crear_transaccion(orden, status, *, amount="100.00", currency="PEN"):
    """Record a provider attempt of the order."""
    return TransaccionPago.objects.create(
        orden_pago=orden,
        transaction_id=f"TXN-{orden.numero}",
        order_number=orden.numero,
        amount=Decimal(amount),
        currency=currency,
        status=status,
    )


def _crear_aprobacion(orden, actor, estado, *, monto="100.00", moneda="PEN"):
    """Record the audited evidence of a manual payment."""
    return AprobacionPagoManual.objects.create(
        orden_pago=orden,
        actor=actor,
        canal=CanalPagoManual.TRANSFERENCIA_BANCARIA,
        referencia=f"REF-{orden.numero}",
        monto=Decimal(monto),
        moneda=moneda,
        motivo="Abono verificado en la cuenta de la institución",
        estado=estado,
    )


def _dejar_evidencia(orden, evidencia: str, actor) -> None:
    """Attach the evidence of the case to the order."""
    if evidencia == "manual_activa":
        _crear_aprobacion(orden, actor, EstadoAprobacionPagoManual.APROBADA)
    elif evidencia == "manual_anulada":
        _crear_aprobacion(orden, actor, EstadoAprobacionPagoManual.ANULADA)
    elif evidencia == "exito":
        _crear_transaccion(orden, IzipayStatus.EXITO)
    elif evidencia == "exito_monto":
        _crear_transaccion(orden, IzipayStatus.EXITO, amount="50.00")
    elif evidencia == "exito_moneda":
        _crear_transaccion(orden, IzipayStatus.EXITO, currency="USD")
    elif evidencia == "intento":
        _crear_transaccion(orden, IzipayStatus.PENDIENTE)
    else:
        _crear_transaccion(orden, IzipayStatus.FALLIDO)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("nombre", "estado", "evidencia", "origen", "tiene_evidencia", "pagada"),
    CASOS,
    ids=[caso[0] for caso in CASOS],
)
def test_el_estado_la_evidencia_y_la_fecha_no_se_contradicen(
    nombre, estado, evidencia, origen, tiene_evidencia, pagada
):
    """
    GIVEN: an order in one state, carrying one kind of evidence
    WHEN:  the canonical evidence predicate is consulted
    THEN:  the derived origin, the evidence flag and the payment date agree
           with the state of the order
    """
    actor = _crear_usuario()
    orden = _crear_orden(estado, nombre)
    _dejar_evidencia(orden, evidencia, actor)

    servicio = EvidenciaPagoService()

    assert servicio.tiene_evidencia_pago(orden) is tiene_evidencia
    assert servicio.origen_pago(orden) == origen

    # The payment date exists EXACTLY for a paid order.
    assert (orden.pagada_en is not None) is pagada


@pytest.mark.django_db
def test_la_proyeccion_masiva_coincide_con_el_predicado_de_cada_orden():
    """
    GIVEN: a page of orders covering the whole cross product
    WHEN:  the bulk projection and the per-order predicate are consulted
    THEN:  both answer the SAME origin for every order of the page
    """
    actor = _crear_usuario()
    ordenes = {}

    for nombre, estado, evidencia, _origen, _tiene, _pagada in CASOS:
        orden = _crear_orden(estado, nombre)
        _dejar_evidencia(orden, evidencia, actor)
        ordenes[str(orden.id)] = orden

    servicio = EvidenciaPagoService()
    proyeccion = EvidenciaPagoService.origenes_por_ordenes(ordenes)

    assert set(proyeccion) == set(ordenes)
    for orden_id, orden in ordenes.items():
        assert proyeccion[orden_id] == servicio.origen_pago(orden)


@pytest.mark.django_db
def test_la_evidencia_de_una_orden_no_contamina_a_las_otras():
    """
    GIVEN: two orders of the SAME amount, one of them paid manually
    WHEN:  the origins of both are projected
    THEN:  only the paid one answers MANUAL — the evidence of an order never
           proves the payment of another one
    """
    actor = _crear_usuario()

    pagada = _crear_orden(PAGADA, "cont1")
    _crear_aprobacion(pagada, actor, EstadoAprobacionPagoManual.APROBADA)
    pendiente = _crear_orden(PENDIENTE, "cont2")

    ordenes = {str(pagada.id): pagada, str(pendiente.id): pendiente}
    proyeccion = EvidenciaPagoService.origenes_por_ordenes(ordenes)

    assert proyeccion[str(pagada.id)] == MANUAL
    assert proyeccion[str(pendiente.id)] == SIN_PAGO
