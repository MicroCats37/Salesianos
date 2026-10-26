"""
Integration tests — commands of the competition (Phase 1).

The competition is the aggregate root of the bracket: it owns the identity
(event + discipline + category + name), the single date of the bracket and
the lifecycle PLANIFICADA → EN_CURSO → FINALIZADA.

The tests go through the orchestrator (the public async façade): the
controller of Phase 3 will use exactly the same entry points.
"""
from datetime import date

import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.exceptions import (
    CompetenciaDuplicadaError,
    CompetenciaNotFoundError,
    DeleteNotAllowedError,
    InvalidScheduleError,
    InvalidStateTransitionError,
    ResourceChangedError,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaCreateData,
    CompetenciaUpdateData,
)

FECHA_VALIDA = date(2026, 11, 16)
FECHA_FUERA_DEL_EVENTO = date(2026, 12, 31)


def _crear(orquestador, actor, evento, disciplina, categoria, **kwargs):
    """Create a competition through the orchestrator."""
    data = CompetenciaCreateData(
        evento_id=str(evento.id),
        disciplina_id=str(disciplina.id),
        categoria_id=str(categoria.id),
        nombre=kwargs.get("nombre", "Eliminatoria F7"),
        fecha=kwargs.get("fecha", FECHA_VALIDA),
    )
    return async_to_sync(orquestador.crear_competencia_proceso)(data, actor)


# ── Identity and date ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_se_crea_con_identidad_fecha_y_version(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: an unused combination WHEN: it is created THEN: it keeps them."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    assert resultado.estado == "PLANIFICADA"
    assert resultado.version == 1
    assert resultado.fecha == FECHA_VALIDA
    assert resultado.nombre == "Eliminatoria F7"
    assert resultado.evento_id == str(evento_competencia.id)
    assert resultado.disciplina_id == str(disciplina_competencia.id)
    assert resultado.categoria_id == str(categoria_competencia.id)


@pytest.mark.django_db
def test_competencia_duplicada_es_rechazada_sin_importar_mayusculas(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: the same identity WHEN: it is created again THEN: it conflicts."""
    _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
        nombre="Eliminatoria F7",
    )

    with pytest.raises(CompetenciaDuplicadaError):
        _crear(
            orquestador_competencias,
            usuario_admin_competencias,
            evento_competencia,
            disciplina_competencia,
            categoria_competencia,
            nombre="eliminatoria f7",
        )


@pytest.mark.django_db
def test_competencia_con_fecha_fuera_del_evento_es_rechazada(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a day outside the event WHEN: it is created THEN: it is invalid."""
    with pytest.raises(InvalidScheduleError):
        _crear(
            orquestador_competencias,
            usuario_admin_competencias,
            evento_competencia,
            disciplina_competencia,
            categoria_competencia,
            fecha=FECHA_FUERA_DEL_EVENTO,
        )


@pytest.mark.django_db
def test_competencia_inexistente_da_404(
    orquestador_competencias,
    usuario_admin_competencias,
):
    """GIVEN: an unknown competition WHEN: it is edited THEN: it does not exist."""
    with pytest.raises(CompetenciaNotFoundError):
        async_to_sync(orquestador_competencias.actualizar_competencia_proceso)(
            "6f0a1f8e-0000-4000-8000-000000000000",
            CompetenciaUpdateData(nombre="No existe"),
            usuario_admin_competencias,
        )


# ── Lifecycle ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_avanza_de_planificada_a_finalizada(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a planned competition WHEN: it starts and finishes THEN: it advances."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    en_curso = async_to_sync(
        orquestador_competencias.cambiar_estado_competencia_proceso
    )(str(resultado.id), "EN_CURSO", usuario_admin_competencias)
    assert en_curso.estado == "EN_CURSO"
    assert en_curso.version == resultado.version + 1

    finalizada = async_to_sync(
        orquestador_competencias.cambiar_estado_competencia_proceso
    )(str(resultado.id), "FINALIZADA", usuario_admin_competencias)
    assert finalizada.estado == "FINALIZADA"


@pytest.mark.django_db
def test_competencia_se_puede_cancelar_antes_de_finalizar(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a running competition WHEN: it is cancelled THEN: it is terminal."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )
    async_to_sync(orquestador_competencias.cambiar_estado_competencia_proceso)(
        str(resultado.id), "EN_CURSO", usuario_admin_competencias
    )

    cancelada = async_to_sync(
        orquestador_competencias.cambiar_estado_competencia_proceso
    )(str(resultado.id), "CANCELADA", usuario_admin_competencias)
    assert cancelada.estado == "CANCELADA"

    with pytest.raises(InvalidStateTransitionError):
        async_to_sync(orquestador_competencias.cambiar_estado_competencia_proceso)(
            str(resultado.id), "EN_CURSO", usuario_admin_competencias
        )


@pytest.mark.django_db
def test_transicion_invalida_de_competencia_es_rechazada(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a planned competition WHEN: it is finished at once THEN: invalid."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    with pytest.raises(InvalidStateTransitionError):
        async_to_sync(orquestador_competencias.cambiar_estado_competencia_proceso)(
            str(resultado.id), "FINALIZADA", usuario_admin_competencias
        )


@pytest.mark.django_db
def test_cambio_de_estado_repetido_es_idempotente(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a running competition WHEN: it is started again THEN: no write."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )
    en_curso = async_to_sync(
        orquestador_competencias.cambiar_estado_competencia_proceso
    )(str(resultado.id), "EN_CURSO", usuario_admin_competencias)

    repetido = async_to_sync(
        orquestador_competencias.cambiar_estado_competencia_proceso
    )(str(resultado.id), "EN_CURSO", usuario_admin_competencias)

    assert repetido.estado == "EN_CURSO"
    assert repetido.version == en_curso.version


# ── Update, audit and optimistic lock ────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_se_actualiza_y_queda_auditada(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a competition WHEN: it is renamed THEN: the change is audited."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    actualizado = async_to_sync(
        orquestador_competencias.actualizar_competencia_proceso
    )(
        str(resultado.id),
        CompetenciaUpdateData(nombre="Eliminatoria F7 Edition"),
        usuario_admin_competencias,
        "Correccion administrativa del nombre",
    )

    assert actualizado.nombre == "Eliminatoria F7 Edition"
    assert actualizado.version == resultado.version + 1

    from modules.competencias.domain.models import Competencia

    registro = Competencia.objects.get(id=resultado.id).history.latest("history_date")
    assert registro.history_user_id == usuario_admin_competencias.id
    assert registro.history_change_reason == "Correccion administrativa del nombre"


@pytest.mark.django_db
def test_actualizar_con_version_obsoleta_falla_sin_efectos_parciales(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a stale version WHEN: it is edited THEN: it conflicts."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    async_to_sync(orquestador_competencias.actualizar_competencia_proceso)(
        str(resultado.id),
        CompetenciaUpdateData(nombre="Primer cambio"),
        usuario_admin_competencias,
        None,
        resultado.version,
    )

    with pytest.raises(ResourceChangedError):
        async_to_sync(orquestador_competencias.actualizar_competencia_proceso)(
            str(resultado.id),
            CompetenciaUpdateData(nombre="Segundo cambio"),
            usuario_admin_competencias,
            None,
            resultado.version,
        )

    from modules.competencias.domain.models import Competencia

    assert Competencia.objects.get(id=resultado.id).nombre == "Primer cambio"


# ── Guarded deletion ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_sin_uso_se_puede_eliminar(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a competition that was never used WHEN: it is deleted THEN: it goes."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )

    async_to_sync(orquestador_competencias.eliminar_competencia_proceso)(
        str(resultado.id), usuario_admin_competencias
    )

    from modules.competencias.domain.models import Competencia

    assert not Competencia.objects.filter(id=resultado.id).exists()


@pytest.mark.django_db
def test_competencia_con_equipos_no_se_puede_eliminar(
    orquestador_competencias,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
    equipo_competencia,
):
    """GIVEN: a competition with teams WHEN: it is deleted THEN: it is refused."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )
    async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(resultado.id),
        str(equipo_competencia.id),
        1,
        usuario_admin_competencias,
    )

    with pytest.raises(DeleteNotAllowedError):
        async_to_sync(orquestador_competencias.eliminar_competencia_proceso)(
            str(resultado.id), usuario_admin_competencias
        )


@pytest.mark.django_db
def test_competencia_con_historia_no_se_puede_eliminar(
    orquestador_competencias,
    usuario_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """GIVEN: a competition already changed WHEN: it is deleted THEN: refused."""
    resultado = _crear(
        orquestador_competencias,
        usuario_admin_competencias,
        evento_competencia,
        disciplina_competencia,
        categoria_competencia,
    )
    async_to_sync(orquestador_competencias.actualizar_competencia_proceso)(
        str(resultado.id),
        CompetenciaUpdateData(nombre="Eliminatoria F7 renombrada"),
        usuario_admin_competencias,
    )

    with pytest.raises(DeleteNotAllowedError):
        async_to_sync(orquestador_competencias.eliminar_competencia_proceso)(
            str(resultado.id), usuario_admin_competencias
        )
