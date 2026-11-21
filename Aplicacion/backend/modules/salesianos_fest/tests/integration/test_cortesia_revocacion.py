"""La REVOCACIÓN de una cortesía: auditada, idempotente y sin hechos financieros.

GIVEN  una cortesía ACTIVA con su derecho
WHEN   se revoca con un motivo
THEN   el acta y el derecho quedan `REVOCADOS`, el motivo queda auditado, y la
       repetición NO es un error (`FR-05` §2.3, `RN-P05`, `RN-P08`).

Change: `administracion-pases-alta-directa` · Apply C
"""

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.constants import (
    EstadoCortesiaPase,
    EstadoDerechoPase,
)
from modules.salesianos_fest.domain.exceptions import (
    ActorRequeridoError,
    CortesiaMotivoInvalidoError,
    CortesiaNoEncontradaError,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.salesianos_fest.domain.schemas.pase_schemas import RevocarCortesiaData
from modules.salesianos_fest.domain.services.flujos.cortesia_flujo import CortesiaFlujo

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def flujo(injector):
    """El flujo de cortesías, resuelto por el inyector real."""
    return injector.get(CortesiaFlujo)


def _intencion(cortesia_id, motivo="Solicitud del beneficiario para su baja."):
    """La intención de revocar una cortesía."""
    return RevocarCortesiaData(
        cortesia_id=str(cortesia_id),
        motivo=motivo,
    )


# ── El acta revocada ────────────────────────────────────────────────────────


def test_la_revocacion_audita_el_acta_y_el_derecho(
    flujo, cortesia_pase, usuario_admin
):
    """GIVEN una cortesía ACTIVA
    WHEN  se revoca con un motivo
    THEN  el acta y el derecho quedan `REVOCADOS` y el motivo queda escrito
       (`RN-P05`).
    """
    resultado = async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    assert resultado.estado == EstadoCortesiaPase.REVOCADA
    assert resultado.motivo_revocacion == "Solicitud del beneficiario para su baja."
    assert resultado.revocado_en is not None
    assert resultado.ya_revocado is False

    cortesia_pase.refresh_from_db()
    assert cortesia_pase.estado == EstadoCortesiaPase.REVOCADA
    assert cortesia_pase.motivo_revocacion == "Solicitud del beneficiario para su baja."

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)
    assert derecho.estado == EstadoDerechoPase.REVOCADO
    assert derecho.motivo_revocacion == "Solicitud del beneficiario para su baja."


def test_la_revocacion_conserva_el_motivo_del_otorgamiento(
    flujo, cortesia_pase, usuario_admin
):
    """GIVEN una cortesía con motivo de otorgamiento
    WHEN  se revoca
    THEN  los DOS motivos se conservan: son hechos de auditoría distintos.
    """
    resultado = async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    assert resultado.motivo == "Invitación del inteligible."
    assert resultado.motivo_revocacion == "Solicitud del beneficiario para su baja."


# ── La idempotencia ─────────────────────────────────────────────────────────


def test_la_revocacion_es_idempotente(flujo, cortesia_pase, usuario_admin):
    """GIVEN una cortesía YA revocada
    WHEN  se revoca otra vez
    THEN  NO es un error: devuelve el mismo estado final con
       `ya_revocado=True` (`FR-05` §2.3).
    """
    async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )
    cortesia_pase.refresh_from_db()
    revocado_en = cortesia_pase.revocado_en

    repetida = async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    assert repetida.ya_revocado is True
    assert repetida.estado == EstadoCortesiaPase.REVOCADA
    assert repetida.revocado_en == revocado_en


# ── Las reglas de la revocación ─────────────────────────────────────────────


def test_la_revocacion_exige_motivo(flujo, cortesia_pase, usuario_admin):
    """GIVEN una revocación SIN motivo
    WHEN  se intenta revocar
    THEN  se rechaza con `CORTESIA_MOTIVO_INVALIDO`: sin motivo no hay
       auditoría (`RN-P05`).
    """
    with pytest.raises(CortesiaMotivoInvalidoError):
        async_to_sync(flujo.revocar_cortesia)(
            _intencion(cortesia_pase.id, motivo=""),
            usuario_admin,
        )


def test_una_cortesia_inexistente_no_se_revoca(flujo, usuario_admin):
    """GIVEN un acta que no existe
    WHEN  se intenta revocar
    THEN  se rechaza con `CORTESIA_NO_ENCONTRADA` (404).
    """
    from uuid import uuid4

    with pytest.raises(CortesiaNoEncontradaError):
        async_to_sync(flujo.revocar_cortesia)(
            _intencion(uuid4()),
            usuario_admin,
        )


def test_sin_cuenta_no_hay_revocacion(flujo, cortesia_pase):
    """GIVEN una petición SIN cuenta
    WHEN  se intenta revocar
    THEN  se rechaza con `ACTOR_REQUERIDO` (401): la revocación es un acto
       administrativo y siempre tiene ACTOR (`RN-P05`).
    """
    with pytest.raises(ActorRequeridoError):
        async_to_sync(flujo.revocar_cortesia)(
            _intencion(cortesia_pase.id),
            None,
        )


# ── Lo que la revocación NO toca ────────────────────────────────────────────


def test_la_revocacion_no_crea_hechos_financieros(
    flujo, cortesia_pase, usuario_admin
):
    """GIVEN una cortesía revocada
    WHEN  se cuentan los hechos financieros
    THEN  NO hay ninguna compra, orden ni transacción nueva: la cortesía no
       los tiene y la revocación tampoco los crea (`RN-P05`).
    """
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago, TransaccionPago

    compras_antes = Compra.objects.count()
    ordenes_antes = OrdenPago.objects.count()
    transacciones_antes = TransaccionPago.objects.count()

    async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    assert Compra.objects.count() == compras_antes
    assert OrdenPago.objects.count() == ordenes_antes
    assert TransaccionPago.objects.count() == transacciones_antes


def test_la_revocacion_no_devuelve_el_consumo(flujo, cortesia_pase, usuario_admin):
    """GIVEN un derecho con un consumo YA realizado
    WHEN  se revoca la cortesía
    THEN  `cantidad_consumida` NO baja: la revocación es PERMANENTE y los
       consumos ya occurring quedan (`RN-P08`).
    """
    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)
    derecho.cantidad_consumida = 1
    derecho.save(update_fields=["cantidad_consumida"])

    async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    derecho.refresh_from_db()
    assert derecho.cantidad_consumida == 1
    assert derecho.estado == EstadoDerechoPase.REVOCADO


def test_tras_revocar_la_persona_puede_recibir_otra_cortesia(
    flujo, cortesia_pase, usuario_admin, pase, edicion_con_pases, persona_ajena
):
    """GIVEN una cortesía revocada
    WHEN  se otorga OTRA cortesía del mismo pase a la misma persona
    THEN  se concede: la restricción parcial única es sobre los derechos
       ACTIVOS, y el revocado ya no lo es.
    """
    from modules.salesianos_fest.domain.schemas.pase_schemas import (
        OtorgarCortesiaData,
    )

    async_to_sync(flujo.revocar_cortesia)(
        _intencion(cortesia_pase.id),
        usuario_admin,
    )

    resultado = async_to_sync(flujo.otorgar_cortesia)(
        OtorgarCortesiaData(
            edicion_id=str(edicion_con_pases.id),
            pase_id=str(pase.id),
            persona_id=str(persona_ajena.id),
            motivo="Segunda cortesía, por cortesía.",
        ),
        usuario_admin,
    )

    assert resultado.estado == EstadoCortesiaPase.ACTIVA
