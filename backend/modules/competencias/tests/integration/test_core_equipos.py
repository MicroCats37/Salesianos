"""
Integration tests — commands of the teams registered in the bracket (Phase 1).

Only ACTIVE teams whose enrollment, discipline and category are the ones of
the competition may be registered, and only once. The manual order is
unique among the active entries and every later change is audited.
"""
import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.exceptions import (
    CompetenciaDuplicadaError,
    EquipoNoElegibleError,
    InvalidStateTransitionError,
    ReasonRequiredError,
    ResourceChangedError,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaEquipoUpdateData,
)
from modules.competencias.domain.models import CompetenciaEquipo


def _incorporar(orquestador, competencia, equipo, orden, actor):
    """Register the team in the bracket through the orchestrator."""
    return async_to_sync(orquestador.incorporar_equipo_proceso)(
        str(competencia.id),
        str(equipo.id),
        orden,
        actor,
    )


# ── Eligibility ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_equipo_activo_compatible_se_incorpora_con_su_orden_manual(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: an active compatible team WHEN: it enters THEN: it keeps its order."""
    resultado = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        3,
        usuario_admin_competencias,
    )

    assert resultado.estado == "ACTIVO"
    assert resultado.orden == 3
    assert resultado.equipo_id == str(equipo_competencia.id)
    assert resultado.version == 1


@pytest.mark.django_db
def test_equipo_cancelado_no_es_elegible(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia_cancelado,
):
    """GIVEN: a cancelled team WHEN: it enters THEN: it is not eligible."""
    with pytest.raises(EquipoNoElegibleError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia_cancelado,
            1,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_equipo_de_otra_disciplina_no_es_elegible(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia_disciplina_ajena,
):
    """GIVEN: a team of another discipline WHEN: it enters THEN: it is refused."""
    with pytest.raises(EquipoNoElegibleError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia_disciplina_ajena,
            1,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_equipo_de_otro_evento_no_es_elegible(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia_evento_ajeno,
):
    """GIVEN: a team of another event WHEN: it enters THEN: it is refused."""
    with pytest.raises(EquipoNoElegibleError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia_evento_ajeno,
            1,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_equipo_de_otra_categoria_no_es_elegible(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia_categoria_ajena,
):
    """GIVEN: a team of another category WHEN: it enters THEN: it is refused."""
    with pytest.raises(EquipoNoElegibleError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia_categoria_ajena,
            1,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_equipo_ya_inscrito_no_se_incorpora_dos_veces(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: a team already in the bracket WHEN: it enters again THEN: refused."""
    _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    with pytest.raises(EquipoNoElegibleError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia,
            2,
            usuario_admin_competencias,
        )


# ── Manual order ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_orden_manual_duplicado_entre_equipos_activos_es_rechazado(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: an order already used WHEN: it is reused THEN: it conflicts."""
    _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    with pytest.raises(CompetenciaDuplicadaError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia_2,
            1,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_orden_manual_se_puede_cambiar_con_motivo_y_queda_auditado(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: a team in the bracket WHEN: its order changes THEN: it is audited."""
    entrada = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    actualizado = async_to_sync(orquestador_competencia_equipos.actualizar_equipo_proceso)(
        str(entrada.id),
        CompetenciaEquipoUpdateData(orden=5),
        usuario_admin_competencias,
        "Reordenamiento manual de la siembra",
    )

    assert actualizado.orden == 5
    assert actualizado.version == entrada.version + 1

    registro = CompetenciaEquipo.objects.get(id=entrada.id).history.latest("history_date")
    assert registro.history_user_id == usuario_admin_competencias.id
    assert registro.history_change_reason == "Reordenamiento manual de la siembra"


@pytest.mark.django_db
def test_cambio_de_orden_sin_motivo_es_rechazado(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: a change of the manual order WHEN: it has no motive THEN: refused."""
    entrada = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    with pytest.raises(ReasonRequiredError):
        async_to_sync(orquestador_competencia_equipos.actualizar_equipo_proceso)(
            str(entrada.id),
            CompetenciaEquipoUpdateData(orden=5),
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_equipo_retirado_libera_el_orden(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: a withdrawn team WHEN: another takes its order THEN: it fits."""
    entrada = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    retirado = async_to_sync(orquestador_competencia_equipos.retirar_equipo_proceso)(
        str(entrada.id),
        usuario_admin_competencias,
        "Baja administrativa del equipo",
    )
    assert retirado.estado == "RETIRADO"

    nuevo = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia_2,
        1,
        usuario_admin_competencias,
    )
    assert nuevo.orden == 1


@pytest.mark.django_db
def test_actualizar_con_version_obsoleta_falla(
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: a stale version WHEN: the order changes THEN: it conflicts."""
    entrada = _incorporar(
        orquestador_competencia_equipos,
        competencia,
        equipo_competencia,
        1,
        usuario_admin_competencias,
    )

    with pytest.raises(ResourceChangedError):
        async_to_sync(orquestador_competencia_equipos.actualizar_equipo_proceso)(
            str(entrada.id),
            CompetenciaEquipoUpdateData(orden=4),
            usuario_admin_competencias,
            "Cambio de orden con version obsoleta",
            entrada.version - 1,
        )


# ── Terminal competition ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_cancelada_no_acepta_equipos(
    orquestador_competencias,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    equipo_competencia,
):
    """GIVEN: a cancelled competition WHEN: a team enters THEN: it is refused."""
    async_to_sync(orquestador_competencias.cambiar_estado_competencia_proceso)(
        str(competencia.id),
        "CANCELADA",
        usuario_admin_competencias,
    )

    with pytest.raises(InvalidStateTransitionError):
        _incorporar(
            orquestador_competencia_equipos,
            competencia,
            equipo_competencia,
            1,
            usuario_admin_competencias,
        )
