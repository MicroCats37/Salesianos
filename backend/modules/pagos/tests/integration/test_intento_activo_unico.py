"""
Integration tests of the one-live-attempt guard of the payment attempts.

A live attempt is a PENDIENTE TransaccionPago: it only records that a
provider session was opened for an order. The guard of this phase has two
parts:

- the READ-ONLY preflight (`verificar_intentos_pago`) reports the orders that
  already carry more than one live attempt, WITHOUT deleting any payment
  history,
- the partial unique index of the database REFUSES a second live attempt of
  the same order, and it is installed only when the data is clean.

The legacy state (an order with more than one live attempt) is exactly the
state the index forbids: the tests that need it remove the index temporarily
(`tests/fixtures/legacy_data.py`) and restore it right after.
"""
import json
import uuid
from decimal import Decimal
from importlib import import_module
from io import StringIO

import pytest
from django.apps import apps as django_apps
from django.core.management import call_command
from django.db import IntegrityError, transaction

from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.tests.fixtures.legacy_data import (
    quitar_guard_de_intento_activo,
    restaurar_guard_de_intento_activo,
)

MIGRACION_GUARD = import_module(
    "modules.pagos.migrations.0006_transpaccionpago_intento_activo_unico"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _orden() -> OrdenPago:
    """Create a pending payment order."""
    return OrdenPago.objects.create(
        numero=f"OP-GUARD-{uuid.uuid4().hex[:8]}",
        monto_total=Decimal("100.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PENDIENTE,
    )


def _intento(
    orden_pago: OrdenPago,
    transaction_id: str,
    status: str = IzipayStatus.PENDIENTE,
) -> TransaccionPago:
    """Create an attempt of the given order."""
    return TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id=transaction_id,
        order_number=f"ORDER-{transaction_id}",
        amount=Decimal("100.00"),
        currency="PEN",
        status=status,
    )


def _intentos_heredados(orden_pago: OrdenPago, cuantos: int = 2) -> list:
    """
    Persist the legacy attempts of an order — with the guard removed.

    More than one live attempt of the same order is exactly the state the
    partial unique index forbids: it can only be reproduced with the index
    temporarily removed.
    """
    intentos = []
    quitar_guard_de_intento_activo()
    try:
        for indice in range(cuantos):
            intentos.append(
                _intento(orden_pago, f"INTENTO-HEREDADO-{indice}-{uuid.uuid4().hex[:6]}")
            )
    finally:
        restaurar_guard_de_intento_activo()
    return intentos


def _ejecutar(*args) -> tuple[str, int]:
    """Run the preflight command and return its output and its exit code."""
    salida = StringIO()
    codigo = 0
    try:
        call_command("verificar_intentos_pago", *args, stdout=salida, stderr=salida)
    except SystemExit as error:
        codigo = error.code or 0
    return salida.getvalue(), codigo


# ── Tests: the read-only preflight ──────────────────────────────────────────

@pytest.mark.django_db
def test_el_preflight_no_reporta_una_orden_con_un_solo_intento_vivo():
    """
    GIVEN: an order with a single live attempt
    WHEN:  the preflight runs
    THEN:  no unsafe order is reported and the command exits with 0.
    """
    orden = _orden()
    _intento(orden, f"INTENTO-UNICO-{uuid.uuid4().hex[:8]}")

    salida, codigo = _ejecutar()

    assert codigo == 0
    assert "ORDEN_CON_MULTIPLES_INTENTOS_VIVOS" not in salida
    assert orden.numero not in salida


@pytest.mark.django_db
def test_el_preflight_reporta_la_orden_con_multiples_intentos_vivos():
    """
    GIVEN: a legacy order that carries MORE THAN ONE live attempt
    WHEN:  the preflight runs
    THEN:  the order is reported and the command exits with 1.
    """
    orden = _orden()
    _intentos_heredados(orden)

    salida, codigo = _ejecutar()

    assert codigo == 1
    assert "ORDEN_CON_MULTIPLES_INTENTOS_VIVOS" in salida
    assert orden.numero in salida


@pytest.mark.django_db
def test_el_preflight_no_modifica_ningun_intento():
    """
    GIVEN: a legacy order with more than one live attempt
    WHEN:  the preflight runs
    THEN:  no attempt is retired, cancelled or deleted — the payment history
           is reported, never "repaired" behind the administrator's back.
    """
    orden = _orden()
    intentos = _intentos_heredados(orden)

    _ejecutar()

    for intento in intentos:
        intento.refresh_from_db()
        assert intento.status == IzipayStatus.PENDIENTE
    assert TransaccionPago.objects.filter(orden_pago=orden).count() == 2


@pytest.mark.django_db
def test_el_informe_json_del_preflight_es_estructurado():
    """
    GIVEN: a legacy order with more than one live attempt
    WHEN:  the preflight runs with --json
    THEN:  the report is a JSON document that states the guard is not
           installable yet.
    """
    orden = _orden()
    _intentos_heredados(orden)

    salida, codigo = _ejecutar("--json")

    assert codigo == 1
    informe = json.loads(salida)
    assert informe["guard_instalable"] is False
    assert informe["total"] == 1
    assert informe["resumen"]["ordenes_inseguras"] == 1

    insegura = informe["inseguras"][0]
    assert insegura["tipo"] == "ORDEN_CON_MULTIPLES_INTENTOS_VIVOS"
    assert insegura["numero_orden"] == orden.numero
    assert insegura["intentos_vivos"] == 2
    assert len(insegura["transaction_ids"]) == 2


@pytest.mark.django_db
def test_el_preflight_de_un_datos_limpios_permite_instalar_el_guard():
    """
    GIVEN: an order with a single live attempt
    WHEN:  the preflight runs with --json
    THEN:  the report states that the guard is installable.
    """
    orden = _orden()
    _intento(orden, f"INTENTO-UNICO-{uuid.uuid4().hex[:8]}")

    salida, codigo = _ejecutar("--json")

    assert codigo == 0
    informe = json.loads(salida)
    assert informe["guard_instalable"] is True
    assert informe["total"] == 0
    assert informe["resumen"]["ordenes_con_intento_vivo"] == 1


# ── Tests: the database guard ───────────────────────────────────────────────

@pytest.mark.django_db
def test_la_restriccion_refusa_un_segundo_intento_vivo():
    """
    GIVEN: an order with a live attempt
    WHEN:  a second live attempt of the same order is persisted
    THEN:  the database refuses it — the one-live-attempt invariant holds
           even if the flow is bypassed.
    """
    orden = _orden()
    _intento(orden, f"INTENTO-VIVO-{uuid.uuid4().hex[:8]}")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            _intento(orden, f"INTENTO-DOBLE-{uuid.uuid4().hex[:8]}")


@pytest.mark.django_db
def test_la_restriccion_permite_varios_intentos_cerrados():
    """
    GIVEN: an order with several CLOSED attempts
    WHEN:  they are persisted
    THEN:  the guard does not touch them — the audit trail of the order keeps
           every attempt it ever had.
    """
    orden = _orden()
    for status in (
        IzipayStatus.CANCELADO,
        IzipayStatus.FALLIDO,
        IzipayStatus.EXITO,
    ):
        _intento(
            orden,
            f"INTENTO-CERRADO-{status}-{uuid.uuid4().hex[:6]}",
            status=status,
        )

    assert TransaccionPago.objects.filter(orden_pago=orden).count() == 3


@pytest.mark.django_db
def test_la_restriccion_permite_reabrir_el_intento_vivo():
    """
    GIVEN: an order with a live attempt
    WHEN:  the live attempt is retired and a fresh one is created
    THEN:  the guard allows it — the flow retires before it creates.
    """
    orden = _orden()
    vivo = _intento(orden, f"INTENTO-VIVO-{uuid.uuid4().hex[:8]}")

    vivo.status = IzipayStatus.CANCELADO
    vivo.save(update_fields=["status", "updated_at"])

    nuevo = _intento(orden, f"INTENTO-NUEVO-{uuid.uuid4().hex[:8]}")

    assert nuevo.status == IzipayStatus.PENDIENTE
    assert (
        TransaccionPago.objects.filter(
            orden_pago=orden, status=IzipayStatus.PENDIENTE
        ).count()
        == 1
    )


# ── Tests: the gate of the migration ────────────────────────────────────────

@pytest.mark.django_db
def test_el_guard_de_la_migracion_rechaza_una_orden_insegura():
    """
    GIVEN: a legacy order with more than one live attempt
    WHEN:  the guard of the migration runs
    THEN:  it refuses the installation of the index and points to the preflight.
    """
    orden = _orden()
    quitar_guard_de_intento_activo()
    try:
        _intento(orden, f"INTENTO-HEREDADO-1-{uuid.uuid4().hex[:6]}")
        _intento(orden, f"INTENTO-HEREDADO-2-{uuid.uuid4().hex[:6]}")

        with pytest.raises(RuntimeError) as error:
            MIGRACION_GUARD.exigir_datos_limpios(django_apps, None)
    finally:
        restaurar_guard_de_intento_activo()

    assert "verificar_intentos_pago" in str(error.value)


@pytest.mark.django_db
def test_el_guard_de_la_migracion_acepta_una_orden_limpia():
    """
    GIVEN: an order with a single live attempt
    WHEN:  the guard of the migration runs
    THEN:  it accepts the data — the index can be installed.
    """
    orden = _orden()
    _intento(orden, f"INTENTO-UNICO-{uuid.uuid4().hex[:8]}")

    MIGRACION_GUARD.exigir_datos_limpios(django_apps, None)
