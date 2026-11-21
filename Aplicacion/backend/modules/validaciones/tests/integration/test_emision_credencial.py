"""La EMISIÓN de una credencial de puerta: derivada, one-shot y secreta.

GIVEN  un derecho de entrada (comprado o de cortesía)
WHEN   se emite su credencial
THEN   el tipo y la operación los DERIVA el módulo dueño, el código es un
       secreto de una sola entrega y una segunda emisión NO se permite
       (`FR-05` §1, `RN-U04`).

Change: `administracion-pases-alta-directa` · Apply C
"""

import pytest
from asgiref.sync import async_to_sync

from core.exceptions import ConflictError
from modules.salesianos_fest.domain.exceptions import (
    PaseBeneficiarioNoEncontradoError,
)
from modules.validaciones.domain.models import Ticket, ValidacionTicket
from modules.validaciones.domain.schemas.validacion_schemas import EmitirTicketData
from modules.validaciones.domain.services.flujos.emitir_ticket_flujo import (
    EmitirTicketFlujo,
)

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def flujo(injector):
    """El flujo de emisión, resuelto por el inyector real."""
    return injector.get(EmitirTicketFlujo)


def _peticion(derecho_id):
    """La intención de emitir la credencial de un derecho."""
    return EmitirTicketData(derecho_id=str(derecho_id))


# ── El tipo DERIVADO ────────────────────────────────────────────────────────


def test_la_emision_deriva_el_tipo_de_una_cortesia(flujo, cortesia_pase):
    """GIVEN un derecho de CORTESÍA
    WHEN  se emite su credencial
    THEN  el tipo es `ENTRADA_CORTESIA` y la operación `INGRESO`: el dueño del
       derecho decide qué credencial corresponde (`RN-U04`).
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    resultado = async_to_sync(flujo._emitir)(_peticion(derecho.id))

    assert resultado.tipo_derecho == "ENTRADA_CORTESIA"
    assert resultado.operacion == "INGRESO"
    assert resultado.edicion_id == str(cortesia_pase.edicion_id)


def test_la_emision_deriva_el_tipo_de_una_compra(flujo, beneficiario_pase):
    """GIVEN un derecho COMPRADO
    WHEN  se emite su credencial
    THEN  el tipo es `PASE` y la operación `INGRESO`.
    """
    resultado = async_to_sync(flujo._emitir)(_peticion(beneficiario_pase.id))

    assert resultado.tipo_derecho == "PASE"
    assert resultado.operacion == "INGRESO"


def test_la_emision_deriva_el_tipo_del_derecho_y_no_del_cliente(
    flujo, cortesia_pase, beneficiario_pase
):
    """GIVEN el MISMO endpoint para dos orígenes distintos
    WHEN  se emiten las dos credenciales
    THEN  cada una lleva el tipo de SU derecho: el cliente no declara el tipo.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho_cortesia = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    cortesia = async_to_sync(flujo._emitir)(_peticion(derecho_cortesia.id))
    compra = async_to_sync(flujo._emitir)(_peticion(beneficiario_pase.id))

    assert cortesia.tipo_derecho == "ENTRADA_CORTESIA"
    assert compra.tipo_derecho == "PASE"


# ── El código es un SECRETO ─────────────────────────────────────────────────


def test_el_codigo_es_impredecible_y_no_deriva_del_derecho(
    flujo, cortesia_pase
):
    """GIVEN una credencial emitida
    WHEN  se lee su código
    THEN  es un código generado, con prefijo, que NO contiene el
       identificador del derecho (`FR-05` §1).
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    resultado = async_to_sync(flujo._emitir)(_peticion(derecho.id))

    assert resultado.codigo.startswith("FEST-")
    assert str(derecho.id) not in resultado.codigo


def test_la_emision_no_registra_el_codigo_en_la_auditoria(flujo, cortesia_pase):
    """GIVEN una credencial emitida
    WHEN  se inspecciona la auditoría
    THEN  NO hay acta de validación: la emisión no es un canje, y el código
       nunca se registra.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    async_to_sync(flujo._emitir)(_peticion(derecho.id))

    assert ValidacionTicket.objects.count() == 0


def test_el_codigo_no_aparece_en_ningun_listado(flujo, cortesia_pase):
    """GIVEN una credencial emitida
    WHEN  se recorre la tabla de credenciales
    THEN  el código SÓLO está en su fila: no hay listados que lo publiquen.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    resultado = async_to_sync(flujo._emitir)(_peticion(derecho.id))

    credenciales = list(Ticket.objects.all())
    assert len(credenciales) == 1
    assert credenciales[0].codigo == resultado.codigo


# ── El one-shot ─────────────────────────────────────────────────────────────


def test_la_emision_es_one_shot_por_derecho(flujo, cortesia_pase):
    """GIVEN un derecho con una credencial VIGENTE
    WHEN  se emite OTRA credencial para ese mismo derecho
    THEN  se rechaza con `CONFLICT` (409): dos códigos vivos para la misma
       persona duplicarían el acceso.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)
    async_to_sync(flujo._emitir)(_peticion(derecho.id))

    with pytest.raises(ConflictError):
        async_to_sync(flujo._emitir)(_peticion(derecho.id))

    assert Ticket.objects.count() == 1


def test_un_derecho_inexistente_no_emite(flujo):
    """GIVEN un derecho que no existe
    WHEN  se intenta emitir su credencial
    THEN  se rechaza con `PASE_BENEFICIARIO_NO_ENCONTRADO` (404).
    """
    from uuid import uuid4

    with pytest.raises(PaseBeneficiarioNoEncontradoError):
        async_to_sync(flujo._emitir)(_peticion(uuid4()))

    assert Ticket.objects.count() == 0


def test_la_emision_no_toca_el_derecho(flujo, cortesia_pase):
    """GIVEN un derecho de cortesía
    WHEN  se emite su credencial
    THEN  el derecho NO cambia: la credencial lo REFERENCIA, no lo modifica
       (`FR-05` §1).
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    async_to_sync(flujo._emitir)(_peticion(derecho.id))

    derecho.refresh_from_db()
    assert derecho.estado == "ACTIVO"
    assert derecho.cantidad_consumida == 0
