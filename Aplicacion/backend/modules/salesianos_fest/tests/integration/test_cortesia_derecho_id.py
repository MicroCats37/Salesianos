"""El `derecho_id` de una cortesía: el identificador del DERECHO de entrada.

GIVEN  un administrador y una edición con un pase vigente
WHEN   otorga una cortesía o consulta el listado administrativo de cortesías
THEN   se publica el identificador EXACTO del `PaseBeneficiario` que la
       cortesía creó —el contra el que se emite la credencial de puerta— y
       NUNCA un identificador inventado: un acta SIN derecho publica `None`.

Change: `administracion-pases-alta-directa` · Apply C (correctivo)
"""

import pytest
from asgiref.sync import async_to_sync
from django.db import connection
from django.test.utils import CaptureQueriesContext

from modules.salesianos_fest.domain.constants import (
    EstadoCortesiaPase,
    EstadoDerechoPase,
    OrigenDerechoPase,
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


def _derecho_de(cortesia):
    """El DERECHO que creó la cortesía."""
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    return PaseBeneficiario.objects.get(cortesia=cortesia)


def _acta_sin_derecho(edicion, pase, persona, actor):
    """Un acta HISTÓRICAMENTE corrupta: existe, pero no tiene derecho.

    Es el único caso en el que `derecho_id` puede ser nulo: el identificador
    ausente se publica como ausente y NUNCA se inventa.
    """
    from modules.salesianos_fest.domain.models import CortesiaPase

    return CortesiaPase.objects.create(
        edicion=edicion,
        pase=pase,
        persona=persona,
        actor_usuario=actor,
        actor_persona=actor.persona_fk,
        motivo="Acta sin derecho (corrupción histórica).",
        estado=EstadoCortesiaPase.ACTIVA,
    )


# ── El otorgamiento ─────────────────────────────────────────────────────────


def test_el_otorgamiento_publica_el_derecho_que_creo(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía otorgada
    WHEN  se lee su resultado
    THEN  publica el identificador del DERECHO que se creó CON ella, en la
       misma transacción (`RN-P05`).
    """
    resultado = async_to_sync(flujo.otorgar_cortesia)(
        _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
        usuario_admin,
    )

    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(persona=persona_ajena)
    assert resultado.derecho_id == str(derecho.id)


def test_el_derecho_publicado_es_el_activo(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía otorgada
    WHEN  se lee su resultado
    THEN  el identificador publicado es el del derecho ACTIVO: la credencial
       se emite contra un derecho vigente.
    """
    resultado = async_to_sync(flujo.otorgar_cortesia)(
        _datos(pase, edicion_con_pases, persona_id=persona_ajena.id),
        usuario_admin,
    )

    from modules.salesianos_fest.domain.models import CortesiaPase

    derecho = _derecho_de(CortesiaPase.objects.get(id=resultado.id))
    assert derecho.estado == EstadoDerechoPase.ACTIVO
    assert str(derecho.id) == resultado.derecho_id


# ── El listado ──────────────────────────────────────────────────────────────


def test_el_listado_publica_el_derecho_de_cada_cortesia(
    flujo, cortesia_pase, edicion_con_pases
):
    """GIVEN una cortesía con su derecho
    WHEN  se lista el alcance administrativo
    THEN  la fila publica el identificador EXACTO de ese derecho.
    """
    resultado = async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    assert len(resultado.items) == 1
    assert resultado.items[0].derecho_id == str(_derecho_de(cortesia_pase).id)


def test_el_listado_publica_el_derecho_revocado(
    flujo, cortesia_pase, edicion_con_pases, usuario_admin
):
    """GIVEN una cortesía REVOCADA
    WHEN  se lista el alcance administrativo
    THEN  la fila publica el identificador del derecho —ahora `REVOCADO`—: la
       revocación es AUDITADA, no un borrado, y el historial conserva el
       identificador del derecho.
    """
    from modules.salesianos_fest.domain.schemas.pase_schemas import RevocarCortesiaData

    derecho_id = str(_derecho_de(cortesia_pase).id)

    async_to_sync(flujo.revocar_cortesia)(
        RevocarCortesiaData(cortesia_id=str(cortesia_pase.id), motivo="Ya no asiste."),
        usuario_admin,
    )

    resultado = async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    assert resultado.items[0].estado == EstadoCortesiaPase.REVOCADA
    assert resultado.items[0].derecho_id == derecho_id


def test_un_acta_sin_derecho_publica_ausente(
    flujo, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN un acta SIN derecho (corrupción histórica)
    WHEN  se lista el alcance administrativo
    THEN  la fila publica `derecho_id = None`: el identificador ausente NUNCA
       se inventa.
    """
    _acta_sin_derecho(edicion_con_pases, pase, persona_ajena, usuario_admin)

    resultado = async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    assert len(resultado.items) == 1
    assert resultado.items[0].derecho_id is None


# ── El N+1 ───────────────────────────────────────────────────────────────────


def test_el_listado_no_consulta_un_derecho_por_fila(
    flujo,
    cortesia_pase,
    edicion_con_pases,
    pase,
    persona,
    persona_otro_participante,
    usuario_admin,
):
    """GIVEN un listado con VARIAS cortesías
    WHEN  se consulta
    THEN  el número de consultas NO crece con las filas: los derechos se
       prefetchean de una vez (`PaseSelector.listar_cortesias`).
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    # Una pasada de calentamiento: la primera llamada puede abrir conexiones.
    async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    with CaptureQueriesContext(connection) as consultas_una:
        async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    _acta_con_derecho(edicion_con_pases, pase, persona, usuario_admin)
    _acta_con_derecho(edicion_con_pases, pase, persona_otro_participante, usuario_admin)

    with CaptureQueriesContext(connection) as consultas_tres:
        async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)

    # TRES filas, las MISMAS consultas: un derecho por fila sería un N+1.
    assert len(consultas_tres) == len(consultas_una)

    # Y el dato es el de VERDAD: tres cortesías, tres derechos publicados.
    resultado = async_to_sync(flujo.listar_cortesias)(edicion_id=edicion_con_pases.id)
    assert len(resultado.items) == 3
    assert all(item.derecho_id for item in resultado.items)
    assert len(PaseBeneficiario.objects.filter(cortesia__isnull=False)) == 3


def _acta_con_derecho(edicion, pase, persona, actor):
    """Un acta CON su derecho ACTIVO, como la que crea el flujo."""
    from modules.salesianos_fest.domain.models import (
        CortesiaPase,
        PaseBeneficiario,
    )

    cortesia = CortesiaPase.objects.create(
        edicion=edicion,
        pase=pase,
        persona=persona,
        actor_usuario=actor,
        actor_persona=actor.persona_fk,
        motivo="Invitación del inteligible.",
        estado=EstadoCortesiaPase.ACTIVA,
    )
    PaseBeneficiario.objects.create(
        edicion=edicion,
        pase=pase,
        persona=persona,
        origen=OrigenDerechoPase.CORTESIA,
        cortesia=cortesia,
        cantidad=1,
        estado=EstadoDerechoPase.ACTIVO,
        motivo="Invitación del inteligible.",
    )
    return cortesia
