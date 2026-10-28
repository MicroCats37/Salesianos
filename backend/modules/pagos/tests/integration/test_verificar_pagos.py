"""
Integration tests of the READ-ONLY diagnosis `verificar_pagos`.

The command answers ONE question: is there any purchase that says "paid"
without a verifiable proof? It NEVER mutates anything: the anomalies it
reports are documented, never "repaired" behind the administrator's back.
"""
import uuid
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import (
    CanalPagoManual,
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import (
    AprobacionPagoManual,
    OrdenPago,
    TransaccionPago,
)
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def usuario(db):
    """An account that can be the actor of an approval."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    persona = Persona.objects.create(
        nombres="Actor",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="M",
    )
    return User.objects.create_user(
        username=f"verificador_{uuid.uuid4().hex[:8]}",
        email=f"verificador_{uuid.uuid4().hex[:8]}@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def orden_pago(db):
    """A payment order of 400 PEN."""
    return OrdenPago.objects.create(
        numero=f"OP-VERIF-{uuid.uuid4().hex[:8]}",
        monto_total=Decimal("400.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PAGADA,
    )


def _compra(orden_pago, estado: str) -> Compra:
    """Create a purchase funded by the given order."""
    return Compra.objects.create(
        descripcion="Compra verificada",
        referencia_externa="VERIF-REF",
        total=Decimal("400.00"),
        estado=estado,
        orden_pago=orden_pago,
    )


def _ejecutar() -> str:
    """Run the command and return its output."""
    salida = StringIO()
    call_command("verificar_pagos", stdout=salida, stderr=salida)
    return salida.getvalue()


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_una_compra_pagada_sin_evidencia_es_reportada(orden_pago):
    """
    GIVEN: a purchase marked as paid whose order has NO evidence
    WHEN:  the diagnosis runs
    THEN:  the anomaly is reported and nothing is mutated.
    """
    compra = _compra(orden_pago, EstadoCompraChoices.PAGADA)

    salida = _ejecutar()

    assert "COMPRA_PAGADA_SIN_EVIDENCIA" in salida
    assert orden_pago.numero in salida

    compra.refresh_from_db()
    assert compra.estado == EstadoCompraChoices.PAGADA


@pytest.mark.django_db
def test_una_orden_pagada_sin_evidencia_es_reportada(orden_pago):
    """
    GIVEN: a paid order without a correlated successful transaction
    WHEN:  the diagnosis runs
    THEN:  the anomaly of the order is reported.
    """
    salida = _ejecutar()

    assert "ORDEN_PAGADA_SIN_EVIDENCIA" in salida
    assert orden_pago.numero in salida


@pytest.mark.django_db
def test_una_transaccion_exitosa_correlacionada_no_es_anomalia(orden_pago):
    """
    GIVEN: a paid order with a CORRELATED successful transaction
    WHEN:  the diagnosis runs
    THEN:  no anomaly is reported about that order.
    """
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id=f"VERIFTX{uuid.uuid4().hex[:8]}",
        order_number=f"VERIFTN{uuid.uuid4().hex[:8]}",
        amount=Decimal("400.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    _compra(orden_pago, EstadoCompraChoices.PAGADA)

    salida = _ejecutar()

    assert "COMPRA_PAGADA_SIN_EVIDENCIA" not in salida
    assert "ORDEN_PAGADA_SIN_EVIDENCIA" not in salida


@pytest.mark.django_db
def test_una_aprobacion_activa_es_evidencia_suficiente(orden_pago, usuario):
    """
    GIVEN: a paid order with an ACTIVE manual approval
    WHEN:  the diagnosis runs
    THEN:  no anomaly is reported and the approval is untouched.
    """
    _compra(orden_pago, EstadoCompraChoices.PAGADA)
    aprobacion = AprobacionPagoManual.objects.create(
        orden_pago=orden_pago,
        actor=usuario,
        canal=CanalPagoManual.YAPE,
        referencia="OP-1",
        monto=Decimal("400.00"),
        moneda="PEN",
        motivo="Abono verificado",
        estado=EstadoAprobacionPagoManual.APROBADA,
    )

    salida = _ejecutar()

    assert "COMPRA_PAGADA_SIN_EVIDENCIA" not in salida
    assert "APROBACION_NO_CORRELACIONADA" not in salida

    aprobacion.refresh_from_db()
    assert aprobacion.estado == EstadoAprobacionPagoManual.APROBADA


@pytest.mark.django_db
def test_una_aprobacion_no_correlacionada_es_reportada(orden_pago, usuario):
    """
    GIVEN: an active approval whose amount differs from the order
    WHEN:  the diagnosis runs
    THEN:  the anomaly is reported — the approval cannot settle that order.
    """
    _compra(orden_pago, EstadoCompraChoices.PAGADA)
    AprobacionPagoManual.objects.create(
        orden_pago=orden_pago,
        actor=usuario,
        canal=CanalPagoManual.EFECTIVO,
        referencia="OP-2",
        monto=Decimal("500.00"),
        moneda="PEN",
        motivo="Monto equivocado",
        estado=EstadoAprobacionPagoManual.APROBADA,
    )

    salida = _ejecutar()

    assert "APROBACION_NO_CORRELACIONADA" in salida


@pytest.mark.django_db
def test_el_informe_json_es_estructurado(orden_pago):
    """
    GIVEN: an anomalous database
    WHEN:  the diagnosis runs with --json
    THEN:  the answer is a JSON document with the anomalies.
    """
    import json

    _compra(orden_pago, EstadoCompraChoices.PAGADA)

    salida = StringIO()
    call_command("verificar_pagos", "--json", stdout=salida, stderr=salida)

    informe = json.loads(salida.getvalue())
    assert informe["total"] >= 1
    assert any(
        anomalia["tipo"] == "COMPRA_PAGADA_SIN_EVIDENCIA"
        for anomalia in informe["anomalias"]
    )
