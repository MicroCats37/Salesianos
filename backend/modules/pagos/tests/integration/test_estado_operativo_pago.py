"""
Integration tests — the payment operator verdict (`EstadoOperativoPagoService`).

The verdict is the ONE answer to "is this payment done?". It is a PURE
function of the facts of ONE order and it is evaluated in a FIXED order: the
first rule that matches wins.

This suite pins the eight codes of the vocabulary and the precedence between
them: a paid order NEVER answers CANCELADA nor VENCIDA, and an expired order
never answers PENDIENTE.

The rules are NEVER the current counts of a database: they are the rules, and
the tests speak of states, not of rows.
"""
from datetime import datetime, timezone

import pytest

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import (
    EstadoOperativoPago,
    OrigenPago,
    OrdenPagoStatus,
)
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)

FECHA_PAGO = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

#: Every code of the vocabulary, with the facts that produce it.
CASOS = [
    (
        "una compra sin orden de pago",
        None,
        EstadoCompraChoices.PENDIENTE,
        OrigenPago.SIN_PAGO,
        None,
        EstadoOperativoPago.SIN_ORDEN,
    ),
    (
        "una compra pagada, liquidada, evidenciada y fechada",
        OrdenPagoStatus.PAGADA,
        EstadoCompraChoices.PAGADA,
        OrigenPago.IZIPAY,
        FECHA_PAGO,
        EstadoOperativoPago.PAGADA,
    ),
    (
        "una compra pagada con la evidencia de una aprobacion manual",
        OrdenPagoStatus.PAGADA,
        EstadoCompraChoices.PAGADA,
        OrigenPago.MANUAL,
        FECHA_PAGO,
        EstadoOperativoPago.PAGADA,
    ),
    (
        "una orden pagada de una compra que sigue pendiente",
        OrdenPagoStatus.PAGADA,
        EstadoCompraChoices.PENDIENTE,
        OrigenPago.IZIPAY,
        FECHA_PAGO,
        EstadoOperativoPago.PAGADA_SIN_LIQUIDAR,
    ),
    (
        "una orden pagada sin evidencia correlacionada",
        OrdenPagoStatus.PAGADA,
        EstadoCompraChoices.PAGADA,
        OrigenPago.SIN_PAGO,
        FECHA_PAGO,
        EstadoOperativoPago.PAGADA_SIN_EVIDENCIA,
    ),
    (
        "una orden pagada y evidenciada sin fecha de pago",
        OrdenPagoStatus.PAGADA,
        EstadoCompraChoices.PAGADA,
        OrigenPago.IZIPAY,
        None,
        EstadoOperativoPago.PAGADA_SIN_FECHA,
    ),
    (
        "una compra y una orden pendientes",
        OrdenPagoStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
        OrigenPago.SIN_PAGO,
        None,
        EstadoOperativoPago.PENDIENTE,
    ),
    (
        "una orden cancelada",
        OrdenPagoStatus.CANCELADA,
        EstadoCompraChoices.PENDIENTE,
        OrigenPago.SIN_PAGO,
        None,
        EstadoOperativoPago.CANCELADA,
    ),
    (
        "una compra cancelada con una orden pendiente",
        OrdenPagoStatus.PENDIENTE,
        EstadoCompraChoices.CANCELADA,
        OrigenPago.SIN_PAGO,
        None,
        EstadoOperativoPago.CANCELADA,
    ),
    (
        "una orden vencida",
        OrdenPagoStatus.VENCIDA,
        EstadoCompraChoices.PENDIENTE,
        OrigenPago.SIN_PAGO,
        None,
        EstadoOperativoPago.VENCIDA,
    ),
]


@pytest.mark.parametrize(
    (
        "escenario",
        "estado_orden",
        "estado_compra",
        "origen_pago",
        "pagada_en",
        "esperado",
    ),
    CASOS,
)
def test_veredicto_operativo_del_pago(
    escenario,
    estado_orden,
    estado_compra,
    origen_pago,
    pagada_en,
    esperado,
):
    """
    GIVEN: the facts of one payment order
    WHEN:  the operator verdict is calculated
    THEN:  the verdict is the expected code.
    """
    veredicto = EstadoOperativoPagoService.calcular(
        estado_orden=estado_orden,
        estado_compra=estado_compra,
        origen_pago=origen_pago,
        pagada_en=pagada_en,
    )

    assert veredicto == esperado, f"El veredicto de {escenario} no es el esperado."


def test_el_vocabulario_del_veredicto_tiene_ocho_codigos():
    """
    GIVEN: the published vocabulary of the operator verdict
    WHEN:  it is read
    THEN:  it holds exactly the eight documented codes.
    """
    assert [codigo for codigo, _etiqueta in EstadoOperativoPago.choices] == [
        "SIN_ORDEN",
        "PAGADA",
        "PAGADA_SIN_LIQUIDAR",
        "PAGADA_SIN_EVIDENCIA",
        "PAGADA_SIN_FECHA",
        "PENDIENTE",
        "CANCELADA",
        "VENCIDA",
    ]


def test_los_ocho_codigos_del_vocabulario_son_alcanzables():
    """
    GIVEN: the table of cases of the suite
    WHEN:  the produced verdicts are collected
    THEN:  EVERY code of the vocabulary is produced by at least one case.
    """
    produced = {caso[-1] for caso in CASOS}

    assert produced == {codigo for codigo, _etiqueta in EstadoOperativoPago.choices}


def test_una_orden_pagada_nunca_responde_cancelada_ni_vencida():
    """
    GIVEN: a paid order whose purchase was cancelled
    WHEN:  the operator verdict is calculated
    THEN:  the verdict is PAGADA_SIN_LIQUIDAR — never CANCELADA.
    """
    veredicto = EstadoOperativoPagoService.calcular(
        estado_orden=OrdenPagoStatus.PAGADA,
        estado_compra=EstadoCompraChoices.CANCELADA,
        origen_pago=OrigenPago.IZIPAY,
        pagada_en=FECHA_PAGO,
    )

    assert veredicto == EstadoOperativoPago.PAGADA_SIN_LIQUIDAR


def test_una_orden_vencida_gana_sobre_la_compra_cancelada():
    """
    GIVEN: an expired order of a cancelled purchase
    WHEN:  the operator verdict is calculated
    THEN:  the verdict is VENCIDA — the ORDER state wins.
    """
    veredicto = EstadoOperativoPagoService.calcular(
        estado_orden=OrdenPagoStatus.VENCIDA,
        estado_compra=EstadoCompraChoices.CANCELADA,
        origen_pago=OrigenPago.SIN_PAGO,
        pagada_en=None,
    )

    assert veredicto == EstadoOperativoPago.VENCIDA


def test_la_evidencia_gana_sobre_la_fecha_de_pago():
    """
    GIVEN: a paid order WITHOUT evidence and WITHOUT a payment date
    WHEN:  the operator verdict is calculated
    THEN:  the verdict is PAGADA_SIN_EVIDENCIA — the missing evidence is the
            first thing the operator must fix.
    """
    veredicto = EstadoOperativoPagoService.calcular(
        estado_orden=OrdenPagoStatus.PAGADA,
        estado_compra=EstadoCompraChoices.PAGADA,
        origen_pago=OrigenPago.SIN_PAGO,
        pagada_en=None,
    )

    assert veredicto == EstadoOperativoPago.PAGADA_SIN_EVIDENCIA
