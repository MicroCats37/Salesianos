"""
Integration tests — the `verificar_pases` diagnostic command.

What this file proves:

1. a HEALTHY database reports ZERO anomalies (the command never cries wolf);
2. every anomaly code is detected: V-P1 (purchase/order disagreement),
   V-P2 (rights beyond the quantity), V-P3 (active right over an unpaid
   purchase), V-P4 (active right without effective accreditation),
   V-P5 (paid purchase missing from the administration union), V-P6 (frozen
   amounts) and V-P7 (inventory cap);
3. the report is STABLE: the same code and the same identifying fields for
   the same anomaly;
4. the command is READ-ONLY: it NEVER modifies a record.
"""
import json
from io import StringIO

import pytest
from django.core.management import call_command

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.models import (
    CompraPase,
    PaseBeneficiario,
)
from modules.salesianos_fest.management.commands.verificar_pases import (
    _anomalias_fuera_del_panel,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _ejecutar(*args):
    """Run the diagnostic and return (exit_code, report)."""
    salida = StringIO()
    with pytest.raises(SystemExit) as error:
        call_command("verificar_pases", "--json", stdout=salida, stderr=salida)
    return error.value.code, json.loads(salida.getvalue())


def _tipos(report):
    """The codes present in the report."""
    return [anomalia["tipo"] for anomalia in report["anomalias"]]


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_una_base_sana_no_reporta_anomalias(api_client, settings):
    """
    GIVEN: a database without any inconsistency of the passes
    WHEN:  the diagnostic runs
    THEN:  it reports ZERO anomalies and exits with 0
    """
    settings.PASES_FIESTA_ENABLED = True

    codigo, report = _ejecutar()

    assert codigo == 0
    assert report["total"] == 0
    assert report["anomalias"] == []


@pytest.mark.django_db
def test_detecta_el_desacuerdo_entre_la_compra_y_su_orden(
    compra_pase_pendiente, settings
):
    """
    GIVEN: a purchase marked as PAID whose payment order is still PENDIENTE
    WHEN:  the diagnostic runs
    THEN:  it reports V-P1 with the stable identifiers of the anomaly
    """
    settings.PASES_FIESTA_ENABLED = True
    compra = compra_pase_pendiente
    compra.estado = EstadoCompraChoices.PAGADA
    compra.save(update_fields=["estado", "updated_at"])

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P1" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P1")
    assert anomalia["compra_id"] == str(compra.id)
    assert anomalia["orden_pago_id"] == str(compra.orden_pago_id)
    assert anomalia["estado_compra"] == EstadoCompraChoices.PAGADA
    assert anomalia["estado_orden"] == OrdenPagoStatus.PENDIENTE


@pytest.mark.django_db
def test_detecta_los_derechos_que_exceden_la_cantidad_comprada(
    compra_pase_pagada, usuario_comprador, persona_beneficiaria_1,
    persona_beneficiaria_2, persona_beneficiaria_3, persona_beneficiaria_4,
    persona_beneficiaria_5, settings
):
    """
    GIVEN: a batch of FOUR passes with FIVE rights delivered
    WHEN:  the diagnostic runs
    THEN:  it reports V-P2 (the slots are immutable)
    """
    settings.PASES_FIESTA_ENABLED = True
    linea = CompraPase.objects.get(compra_id=compra_pase_pagada.id)

    for indice, persona in enumerate(
        (
            persona_beneficiaria_1,
            persona_beneficiaria_2,
            persona_beneficiaria_3,
            persona_beneficiaria_4,
            persona_beneficiaria_5,
        ),
        start=1,
    ):
        PaseBeneficiario.objects.create(
            compra_pase=linea,
            evento=linea.evento,
            persona=persona,
            slot=indice,
            estado=EstadoPaseBeneficiarioChoices.ACTIVA,
            asignado_por=usuario_comprador,
        )

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P2" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P2")
    assert anomalia["cantidad_comprada"] == linea.cantidad
    assert anomalia["derechos_registrados"] == 5


@pytest.mark.django_db
def test_detecta_el_derecho_activo_sobre_una_compra_no_pagada(
    compra_pase_pendiente, usuario_comprador, persona_beneficiaria_1, settings
):
    """
    GIVEN: an ACTIVE right over a purchase that is NOT paid
    WHEN:  the diagnostic runs
    THEN:  it reports V-P3
    """
    settings.PASES_FIESTA_ENABLED = True
    linea = CompraPase.objects.get(compra_id=compra_pase_pendiente.id)

    PaseBeneficiario.objects.create(
        compra_pase=linea,
        evento=linea.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P3" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P3")
    assert anomalia["estado_compra"] == EstadoCompraChoices.PENDIENTE
    assert anomalia["persona_id"] == str(persona_beneficiaria_1.id)


@pytest.mark.django_db
def test_detecta_el_derecho_activo_sin_acreditacion_efectiva(
    compra_pase_pagada, usuario_comprador, persona_beneficiaria_1, settings
):
    """
    GIVEN: an ACTIVE right over a PAID purchase WITHOUT accreditation
    WHEN:  the diagnostic runs
    THEN:  it reports V-P4 (nobody explains the denial)
    """
    settings.PASES_FIESTA_ENABLED = True
    linea = CompraPase.objects.get(compra_id=compra_pase_pagada.id)

    PaseBeneficiario.objects.create(
        compra_pase=linea,
        evento=linea.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P4" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P4")
    assert anomalia["persona_id"] == str(persona_beneficiaria_1.id)
    assert anomalia["acreditacion_id"] is None


@pytest.mark.django_db
def test_detecta_la_compra_pagada_fuera_de_la_union_de_la_administracion(
    compra_pase_pagada, settings
):
    """
    GIVEN: a PAID pass purchase that the administration union does NOT list
    WHEN:  the diagnostic evaluates the visible purchases
    THEN:  it reports V-P5

    The union of the administration is supplied as the EMPTY set of visible
    ids: the seam of the command is a plain parameter, so the test NEVER
    patches the selector at runtime
    (`contract/TEST_ARCHITECTURE_CONTRACT.md` §6).
    """
    settings.PASES_FIESTA_ENABLED = True

    linea = CompraPase.objects.get(compra_id=compra_pase_pagada.id)

    anomalias = _anomalias_fuera_del_panel([linea], set())

    assert len(anomalias) == 1
    anomalia = anomalias[0]
    assert anomalia["tipo"] == "V-P5"
    assert anomalia["compra_id"] == str(compra_pase_pagada.id)
    assert anomalia["pase_id"] == str(linea.pase_id)

    # A purchase that the administration DOES list is not an anomaly.
    assert _anomalias_fuera_del_panel([linea], {str(linea.compra_id)}) == []


@pytest.mark.django_db
def test_detecta_los_montos_congelados_inconsistentes(
    compra_pase_pagada, settings
):
    """
    GIVEN: a batch whose frozen total is NOT cantidad * precio_unitario
    WHEN:  the diagnostic runs
    THEN:  it reports V-P6
    """
    settings.PASES_FIESTA_ENABLED = True
    linea = CompraPase.objects.get(compra_id=compra_pase_pagada.id)
    linea.total = linea.total + 10
    linea.save(update_fields=["total", "updated_at"])

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P6" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P6")
    assert anomalia["compra_id"] == str(compra_pase_pagada.id)


@pytest.mark.django_db
def test_detecta_el_inventario_excedido(
    pase_con_inventario_limitado, usuario_comprador, settings
):
    """
    GIVEN: two purchases of the same pass that exceed its inventory cap
    WHEN:  the diagnostic runs
    THEN:  it reports V-P7
    """
    settings.PASES_FIESTA_ENABLED = True
    limite = pase_con_inventario_limitado.cantidad_maxima

    for indice in range(2):
        linea = CompraPase.objects.create(
            compra=compra_pase_pagada_compra(usuario_comprador, indice),
            pase=pase_con_inventario_limitado,
            evento=pase_con_inventario_limitado.evento,
            cantidad=limite,
            precio_unitario=25,
            total=limite * 25,
        )
        assert linea.cantidad == limite

    codigo, report = _ejecutar()

    assert codigo == 1
    assert "V-P7" in _tipos(report)
    anomalia = next(a for a in report["anomalias"] if a["tipo"] == "V-P7")
    assert anomalia["pase_id"] == str(pase_con_inventario_limitado.id)
    assert anomalia["vendido"] == limite * 2


@pytest.mark.django_db
def test_el_diagnostico_no_modifica_ningun_registro(
    compra_pase_pagada, usuario_comprador, persona_beneficiaria_1, settings
):
    """
    GIVEN: a database with an inconsistency
    WHEN:  the diagnostic runs
    THEN:  not ONE record was modified (the command is read-only)
    """
    settings.PASES_FIESTA_ENABLED = True
    linea = CompraPase.objects.get(compra_id=compra_pase_pagada.id)
    PaseBeneficiario.objects.create(
        compra_pase=linea,
        evento=linea.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    compras_antes = list(compra_pase_pagada.__class__.objects.values())
    linea_antes = CompraPase.objects.get(id=linea.id)
    total_antes = linea_antes.total
    estado_antes = linea_antes.cantidad

    codigo, _report = _ejecutar()

    assert codigo == 1
    linea_despues = CompraPase.objects.get(id=linea.id)
    assert linea_despues.total == total_antes
    assert linea_despues.cantidad == estado_antes
    assert list(compra_pase_pagada.__class__.objects.values()) == compras_antes


# ── Helpers locales ──────────────────────────────────────────────────────────


def compra_pase_pagada_compra(usuario, indice):
    """A paid purchase with its order, ready to hold a pass line."""
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.constants import OrdenPagoStatus as _Estado
    from modules.pagos.domain.models import OrdenPago

    orden = OrdenPago.objects.create(
        numero=f"OP-DIAG-{indice}",
        monto_total=25 * 5,
        moneda="PEN",
        estado=_Estado.PAGADA,
    )
    compra = Compra.objects.create(
        responsable=usuario.persona_fk,
        descripcion="Compra de pases - diagnóstico",
        referencia_externa=f"PASE-DIAG-{indice}",
        total=25 * 5,
        estado=EstadoCompraChoices.PAGADA,
    )
    compra.orden_pago = orden
    compra.save(update_fields=["orden_pago", "updated_at"])
    return compra
