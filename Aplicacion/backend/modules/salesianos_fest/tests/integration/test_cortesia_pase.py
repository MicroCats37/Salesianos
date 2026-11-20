"""La CORTESÍA: un derecho gratuito, auditado y sin hecho financiero.

GIVEN  un administrador y una edición con un pase vigente
WHEN   otorga una cortesía
THEN   se registra un ACTA con actor y motivo, se crea el DERECHO, NO se
       crea ninguna compra, orden ni transacción, y una cortesía NO puede
       duplicar un derecho comprado (`FL-07`, `RN-P05`, `QA-P03`).

**NO EJECUTADO.** La verificación en runtime de este paquete está DIFERIDA
por instrucción explícita del usuario. Ver
`evidence/domains/DOM-03-pases-beneficios-cortesia.md` §6.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.exceptions import (
    ActorRequeridoError,
    CortesiaMotivoInvalidoError,
    PaseDuplicadoError,
    PaseNoDisponibleError,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import OtorgarCortesiaData
from modules.salesianos_fest.domain.services.flujos.cortesia_flujo import CortesiaFlujo

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def flujo(injector):
    """El flujo de cortesías, resuelto por el inyector real."""
    return injector.get(CortesiaFlujo)


def _datos(pase, edicion, persona_id=None, motivo="Invitación del inteligible."):
    """La intención de otorgar una cortesía."""
    return OtorgarCortesiaData(
        edicion_id=str(edicion.id),
        pase_id=str(pase.id),
        persona_id=str(persona_id) if persona_id else None,
        tipo_documento=None if persona_id else "DNI",
        numero_documento=None if persona_id else "30303030",
        nombres="" if persona_id else "Cortesía",
        apellidos="" if persona_id else "De Prueba",
        motivo=motivo,
    )


# ── El acta auditada ────────────────────────────────────────────────────────


def test_la_cortesia_registra_actor_y_motivo(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN un administrador
    WHEN  otorga una cortesía
    THEN  el acta guarda el ACTOR y el MOTIVO (`RN-P05`, `FL-07` paso 2).
    """
    resultado = async_to_sync(flujo.otorgar_cortesia)(
        _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
        usuario_admin,
    )

    assert resultado.motivo == "Invitación del inteligible."
    assert resultado.actor_usuario_id == str(usuario_admin.id)
    assert resultado.estado == "ACTIVA"
    assert resultado.concedido_en is not None


def test_la_cortesia_crea_el_derecho(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía otorgada
    WHEN  se consulta el acta
    THEN  existe un DERECHO ACTIVO de la persona, con origen `CORTESIA`.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    async_to_sync(flujo.otorgar_cortesia)(
        _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
        usuario_admin,
    )

    derecho = PaseBeneficiario.objects.get(persona=persona_ajena)
    assert derecho.origen == "CORTESIA"
    assert derecho.estado == "ACTIVO"
    assert derecho.cortesia is not None


def test_sin_motivo_no_se_registra(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía SIN motivo
    WHEN  se intenta otorgar
    THEN  se rechaza con `CORTESIA_MOTIVO_INVALIDO`: sin motivo no hay
       auditoría (`RN-P05`).
    """
    with pytest.raises(CortesiaMotivoInvalidoError):
        async_to_sync(flujo.otorgar_cortesia)(
            _datos(pase, edicion_con_pases, persona_id=persona_ajena.id, motivo=""),
            usuario_admin,
        )


def test_sin_cuenta_no_hay_cortesia(
    flujo, pase, edicion_con_pases, persona_ajena
):
    """GIVEN una petición SIN cuenta
    WHEN  se intenta otorgar una cortesía
    THEN  se rechaza con `ACTOR_REQUERIDO` (401): una cortesía sin actor no
       es auditable.
    """
    with pytest.raises(ActorRequeridoError):
        async_to_sync(flujo.otorgar_cortesia)(
            _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
            None,
        )


# ── La ausencia de hecho financiero ─────────────────────────────────────────


def test_la_cortesia_no_crea_compra_ni_orden_ni_transaccion(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía otorgada
    WHEN  se cuentan los hechos financieros
    THEN  NO hay ninguna compra nueva, ni orden de pago, ni transacción: no
       se simula un cobro de S/ 0 (`RN-P05`, `FL-07` paso 3).
    """
    from modules.pagos.domain.models import OrdenPago, TransaccionPago

    compras_antes = Compra.objects.count()
    ordenes_antes = OrdenPago.objects.count()
    transacciones_antes = TransaccionPago.objects.count()

    async_to_sync(flujo.otorgar_cortesia)(
        _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
        usuario_admin,
    )

    assert Compra.objects.count() == compras_antes
    assert OrdenPago.objects.count() == ordenes_antes
    assert TransaccionPago.objects.count() == transacciones_antes


def test_el_acta_de_cortesia_no_tiene_compra_ni_orden(
    cortesia_pase, usuario_admin
):
    """GIVEN el acta de una cortesía
    WHEN  se inspecciona su ESQUEMA
    THEN  no tiene ninguna columna que la enlace con una compra, una orden o
       una transacción: la garantía es estructural, no una convención.
    """
    campos = {campo.name for campo in cortesia_pase._meta.get_fields()}

    assert "compra" not in campos
    assert "orden_pago" not in campos
    assert "transaccion" not in campos


# ── La no duplicación ───────────────────────────────────────────────────────


def test_la_cortesia_no_duplica_un_derecho_activo(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin, beneficiario_pase
):
    """GIVEN una persona que YA tiene un derecho ACTIVO de ese pase
    WHEN  se intenta otorgarle una cortesía
    THEN  se rechaza con `PASE_DUPLICADO` (`RN-P07`).
    """
    with pytest.raises(PaseDuplicadoError):
        async_to_sync(flujo.otorgar_cortesia)(
            _datos(pase, edicion_con_pases, persona_id=beneficiario_pase.persona_id),
            usuario_admin,
        )


def test_un_pase_inexistente_no_se_otorga(
    flujo, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN un pase que no existe en la edición
    WHEN  se intenta otorgar la cortesía
    THEN  se rechaza con `PASE_NO_DISPONIBLE`.
    """
    from uuid import uuid4

    with pytest.raises(PaseNoDisponibleError):
        async_to_sync(flujo.otorgar_cortesia)(
            OtorgarCortesiaData(
                edicion_id=str(edicion_con_pases.id),
                pase_id=str(uuid4()),
                persona_id=str(persona_ajena.id),
                motivo="Motivo de la prueba.",
            ),
            usuario_admin,
        )
