"""Agregar, mover y retirar participantes: elegibilidad, duplicados y carreras.

GIVEN  una inscripción con capacidad pagada y un equipo
WHEN   el responsable agrega, mueve o retira participantes
THEN   el servidor verifica SIEMPRE la elegibilidad, la pertenencia a la
       edición, la ausencia de duplicados y la titularidad, y dos
       asignaciones simultáneas NO pueden sobre-suscribir el pool
       (`RN-I05`, `FR-03` §2.1, `QA-I05`).
"""

import asyncio

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.constants import CausaOperativaPool
from modules.salesianos_fest.domain.exceptions import (
    DisciplinaNoPermitidaError,
    EquipoCompletoError,
    EquipoNoEncontradoError,
    InscripcionNoAutorizadaError,
    ParticipanteDuplicadoError,
    ParticipanteNoElegibleError,
    ParticipanteNoEncontradoError,
    PersonaNoEncontradaError,
    SinCuposDisponiblesError,
)
from modules.salesianos_fest.domain.models import (
    Equipo,
    Inscripcion,
    Participacion,
)
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo
from modules.salesianos_fest.domain.services.core.capacidad_core_service import (
    CapacidadCoreService,
)
from modules.salesianos_fest.domain.services.orchestrators.pool_orchestrator import (
    PoolOrchestrator,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real del pool."""
    return injector.get(PoolFlujo)


@pytest.fixture
def orchestrator(injector):
    """El orquestador real del pool."""
    return injector.get(PoolOrchestrator)


@pytest.fixture
def intencion(inscripcion, equipo, persona_participante):
    """La intención de agregar un participante al pool."""
    return ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )


# ── Éxito ────────────────────────────────────────────────────────────────────


def test_agregar_un_participante_lo_mete_en_el_pool(flujo, intencion):
    """GIVEN una inscripción con cupos pagados
    WHEN  el responsable agrega un participante
    THEN  la participación queda ACTIVA y ocupa un cupo.
    """
    pool = async_to_sync(flujo.agregar_participante)(intencion)

    assert pool.causa_operativa == CausaOperativaPool.PARTICIPACION_AGREGADA
    assert len(pool.participaciones) == 1
    assert pool.participaciones[0].ocupa_cupo is True
    assert pool.cupos_asignados == 1
    assert pool.cupos_disponibles == 9


def test_la_persona_se_puede_resolver_por_documento(
    flujo, inscripcion, equipo, persona_participante
):
    """GIVEN una persona que todavía no está en la inscripción
    WHEN  se la identifica por su documento
    THEN  el servidor la resuelve en el padrón y la agrega (`FL-05` paso 2).
    """
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        tipo_documento="DNI",
        numero_documento="33333333",
        equipo_id=equipo.id,
    )

    pool = async_to_sync(flujo.agregar_participante)(intencion)

    assert len(pool.participaciones) == 1
    assert pool.participaciones[0].persona_id == str(persona_participante.id)


def test_una_persona_inexistente_se_rechaza(
    flujo, inscripcion, equipo
):
    """GIVEN un documento que no está en el padrón
    WHEN  se intenta agregar
    THEN  se rechaza con `PERSONA_NO_ENCONTRADA`: el módulo NO crea
       identidades (`FR-03`).
    """
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        tipo_documento="DNI",
        numero_documento="99999999",
        equipo_id=equipo.id,
    )

    with pytest.raises(PersonaNoEncontradaError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0


# ── Rechazos de elegibilidad ────────────────────────────────────────────────


def test_la_disciplina_inactiva_no_es_elegible(
    flujo, inscripcion, disciplina_inactiva, persona_participante, categoria
):
    """GIVEN una disciplina INACTIVA
    WHEN  se intenta agregar un participante a su equipo
    THEN  se rechaza con `PARTICIPANTE_NO_ELEGIBLE` (`RN-I05`).
    """
    equipo = Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_inactiva,
        categoria=categoria,
        nombre="Equipo Inactivo",
    )
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )

    with pytest.raises(ParticipanteNoElegibleError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0


def test_la_disciplina_que_el_paquete_no_permite_se_rechaza(
    flujo, inscripcion, disciplina_otra_edicion, persona_participante, categoria
):
    """GIVEN una disciplina que NO está en el paquete de la inscripción
    WHEN  se intenta agregar un participante
    THEN  se rechaza con `DISCIPLINA_NO_PERMITIDA`.
    """
    equipo = Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_otra_edicion,
        categoria=categoria,
        nombre="Equipo Ajeno",
    )
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )

    with pytest.raises(DisciplinaNoPermitidaError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0


def test_el_equipo_de_otra_inscripcion_no_existe(
    flujo,
    inscripcion,
    persona_participante,
    persona_ajena,
    paquete,
    disciplina,
    categoria,
):
    """GIVEN un equipo de OTRA inscripción
    WHEN  se intenta agregar un participante a ese equipo
    THEN  se rechaza con `EQUIPO_NO_ENCONTRADO`: la inscripción es el
       alcance (`RN-E01`, `RN-I05`).
    """
    otra_inscripcion = Inscripcion.objects.create(
        edicion_id=inscripcion.edicion_id,
        responsable_id=persona_ajena.id,
        paquete_id=inscripcion.paquete_id,
        promocion_id=inscripcion.promocion_id,
        referencia="INS-TEST-OTRA",
        cupos_solicitados=10,
        cupos_pagados=10,
    )
    equipo_ajeno = Equipo.objects.create(
        inscripcion=otra_inscripcion,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Equipo Ajeno",
    )
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo_ajeno.id,
    )

    with pytest.raises(EquipoNoEncontradoError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0


def test_la_modalidad_de_la_disciplina_exige_el_generero(
    flujo, inscripcion, persona_otro_participante, categoria
):
    """GIVEN una disciplina FEMENINA y una persona de género MASCULINO
    WHEN  se intenta agregar
    THEN  se rechaza con `PARTICIPANTE_NO_ELEGIBLE`: la compatibilidad la
       verifica el servidor (`RN-I05`).
    """
    from modules.salesianos_fest.domain.constants import ModalidadDisciplina
    from modules.salesianos_fest.domain.models import Disciplina

    disciplina = Disciplina.objects.create(
        edicion_id=inscripcion.edicion_id,
        nombre="Vóley Femenino",
        slug="voley-femenino",
        modalidad=ModalidadDisciplina.FEMENINO,
        maximo_por_equipo=12,
    )
    from modules.salesianos_fest.domain.models import PaqueteDisciplina

    PaqueteDisciplina.objects.create(paquete_id=inscripcion.paquete_id, disciplina=disciplina)
    equipo = Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Equipo Femenino",
    )
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_otro_participante.id,
        equipo_id=equipo.id,
    )

    with pytest.raises(ParticipanteNoElegibleError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0


def test_el_tope_del_equipo_se_cumple(
    flujo, inscripcion, equipo, persona_participante
):
    """GIVEN un equipo que alcanzó su máximo de participantes
    WHEN  se intenta agregar otro
    THEN  se rechaza con `EQUIPO_COMPLETO` (`RN-I05`: los topes se
       verifican en backend).
    """
    disciplina = equipo.disciplina
    disciplina.maximo_por_equipo = 1
    disciplina.save(update_fields=["maximo_por_equipo"])

    async_to_sync(flujo.agregar_participante)(
        ParticipanteAsignarData(
            inscripcion_id=inscripcion.id,
            persona_id=persona_participante.id,
            equipo_id=equipo.id,
        )
    )

    from modules.usuarios.domain.models import Persona

    otra = Persona.objects.create(
        nombres="Sofía",
        apellidos="Vega",
        tipo_documento="DNI",
        numero_documento="55555555",
    )
    with pytest.raises(EquipoCompletoError):
        async_to_sync(flujo.agregar_participante)(
            ParticipanteAsignarData(
                inscripcion_id=inscripcion.id,
                persona_id=otra.id,
                equipo_id=equipo.id,
            )
        )


def test_la_persona_no_participa_dos_veces_en_la_misma_inscripcion(
    flujo, intencion, persona_participante
):
    """GIVEN un participante ya activo en la inscripción
    WHEN  se intenta agregarlo otra vez
    THEN  se rechaza con `PARTICIPANTE_DUPLICADO` (`QA-I05`).
    """
    async_to_sync(flujo.agregar_participante)(intencion)

    with pytest.raises(ParticipanteDuplicadoError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 1


def test_la_persona_no_se_solapa_en_la_misma_disciplina_de_la_edicion(
    flujo, inscripcion, equipo, persona_participante, edicion_publicada, paquete, persona_ajena
):
    """GIVEN una persona que ya participa en la disciplina desde OTRA
    inscripción de la MISMA edición
    WHEN  se intenta agregarla a esta inscripción
    THEN  se rechaza con `PARTICIPANTE_NO_ELEGIBLE`: el solapamiento se
       verifica en backend (`RN-I05`).
    """
    otra_inscripcion = Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable_id=persona_ajena.id,
        paquete=paquete,
        promocion_id=inscripcion.promocion_id,
        referencia="INS-TEST-SOLAPE",
        cupos_solicitados=10,
        cupos_pagados=10,
    )
    equipo_otro = Equipo.objects.create(
        inscripcion=otra_inscripcion,
        disciplina=equipo.disciplina,
        categoria=equipo.categoria,
        nombre="Equipo Solapado",
    )
    Participacion.objects.create(
        inscripcion=otra_inscripcion,
        persona=persona_participante,
        equipo=equipo_otro,
        edicion=edicion_publicada,
        disciplina=equipo.disciplina,
    )

    with pytest.raises(ParticipanteNoElegibleError):
        async_to_sync(flujo.agregar_participante)(
            ParticipanteAsignarData(
                inscripcion_id=inscripcion.id,
                persona_id=persona_participante.id,
                equipo_id=equipo.id,
            )
        )


# ── Titularidad ─────────────────────────────────────────────────────────────


def test_un_actor_ajeno_no_gestiona_el_pool(
    orchestrator, inscripcion, equipo, persona_participante, usuario_ajeno
):
    """GIVEN una cuenta que NO es la responsable de la inscripción
    WHEN  intenta agregar un participante
    THEN  se rechaza con `INSCRIPCION_NO_AUTORIZADA` (403): ser
       administrador NO sustituye la titularidad (`FR-03` §2.1).
    """
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )

    with pytest.raises(InscripcionNoAutorizadaError):
        async_to_sync(orchestrator.agregar_participante)(
            usuario_ajeno,
            inscripcion.id,
            intencion,
        )

    assert Participacion.objects.count() == 0


def test_el_responsable_gestiona_su_pool(
    orchestrator, inscripcion, equipo, persona_participante, usuario_responsable
):
    """GIVEN la cuenta responsable de la inscripción
    WHEN  agrega un participante
    THEN  la operación se ejecuta.
    """
    intencion = ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )

    pool = async_to_sync(orchestrator.agregar_participante)(
        usuario_responsable,
        inscripcion.id,
        intencion,
    )

    assert pool.cupos_asignados == 1


# ── Movimiento y retirada ───────────────────────────────────────────────────


def test_mover_reeasigna_el_cupo_sin_dejar_saldo_negativo(
    flujo, intencion, inscripcion, persona_otro_participante
):
    """GIVEN un participante que ocupa el último cupo disponible
    WHEN  se mueve su cupo a otra persona
    THEN  el cupo cambia de manos en la MISMA transacción y el disponible
       nunca es negativo (`FL-05` paso 4, `RN-I04`).
    """
    inscripcion.cupos_pagados = 1
    inscripcion.save(update_fields=["cupos_pagados"])

    async_to_sync(flujo.agregar_participante)(intencion)
    participacion = Participacion.objects.get()

    pool = async_to_sync(flujo.agregar_participante)(
        ParticipanteAsignarData(
            inscripcion_id=inscripcion.id,
            persona_id=persona_otro_participante.id,
            equipo_id=intencion.equipo_id,
            reemplaza_participacion_id=participacion.id,
        )
    )

    assert pool.causa_operativa == CausaOperativaPool.CUPO_REASIGNADO
    assert pool.cupos_asignados == 1
    assert pool.cupos_disponibles == 0
    assert pool.cupos_disponibles >= 0
    assert Participacion.objects.count() == 2
    assert Participacion.objects.filter(estado="ACTIVA").count() == 1


def test_retirar_una_participacion_inexistente_se_rechaza(
    flujo, inscripcion
):
    """GIVEN un identificador de participación que no existe
    WHEN  se intenta retirar
    THEN  se rechaza con `PARTICIPANTE_NO_ENCONTRADO` (404).
    """
    from uuid import uuid4

    with pytest.raises(ParticipanteNoEncontradoError):
        async_to_sync(flujo.retirar_participante)(inscripcion.id, uuid4())


def test_no_se_puede_retirar_la_participacion_de_otra_inscripcion(
    flujo,
    intencion,
    inscripcion,
    persona_participante,
    edicion_publicada,
    paquete,
    persona_ajena,
):
    """GIVEN una participación que pertenece a otra inscripción
    WHEN  se intenta retirar desde esta inscripción
    THEN  se rechaza: el recurso es de su propia inscripción.
    """
    async_to_sync(flujo.agregar_participante)(intencion)
    participacion = Participacion.objects.get()

    otra_inscripcion = Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable_id=persona_ajena.id,
        paquete=paquete,
        promocion_id=inscripcion.promocion_id,
        referencia="INS-TEST-OTRA-2",
        cupos_solicitados=10,
        cupos_pagados=10,
    )

    with pytest.raises(ParticipanteNoEncontradoError):
        async_to_sync(flujo.retirar_participante)(
            otra_inscripcion.id,
            participacion.id,
        )


# ── Carrera ─────────────────────────────────────────────────────────────────


def test_la_reserva_de_cupo_es_una_sentencia_atomica_condicional(
    injector, inscripcion
):
    """GIVEN una inscripción con UN solo cupo disponible
    WHEN  se intenta reservar dos veces
    THEN  la SEGUNDA reserva falla: la condición `cupos_asignados <
       cupos_pagados` viaja DENTRO de la sentencia, así que la base de
       datos —no la aplicación— decide quién entra (`QA-I05`).
    """
    inscripcion.cupos_pagados = 1
    inscripcion.save(update_fields=["cupos_pagados"])

    capacidad_core = injector.get(CapacidadCoreService)

    assert capacidad_core.reservar_cupo(inscripcion.id) is True
    assert capacidad_core.reservar_cupo(inscripcion.id) is False

    inscripcion.refresh_from_db()
    assert inscripcion.cupos_asignados == 1
    assert inscripcion.cupos_asignados <= inscripcion.cupos_pagados


@pytest.mark.django_db(transaction=True)
def test_dos_asignaciones_simultaneas_no_sobre_suscriben(
    injector, inscripcion, equipo, persona_participante, persona_otro_participante
):
    """GIVEN un ÚNICO cupo disponible y dos peticiones simultáneas
    WHEN  ambas intentan asignar
    THEN  el pool NO queda sobre-suscrito (`QA-I05`, `RN-I03`).

    El motor de pruebas es SQLite en memoria con CACHÉ COMPARTIDA: dos
    escritores simultáneos pueden recibir un bloqueo del motor. Lo que NO
    puede pasar es el sobre-suscripción: ésa es la invariante que se
    comprueba.
    """
    inscripcion.cupos_pagados = 1
    inscripcion.save(update_fields=["cupos_pagados"])

    flujo = injector.get(PoolFlujo)

    async def _simultaneas():
        return await asyncio.gather(
            flujo.agregar_participante(
                ParticipanteAsignarData(
                    inscripcion_id=inscripcion.id,
                    persona_id=persona_participante.id,
                    equipo_id=equipo.id,
                )
            ),
            flujo.agregar_participante(
                ParticipanteAsignarData(
                    inscripcion_id=inscripcion.id,
                    persona_id=persona_otro_participante.id,
                    equipo_id=equipo.id,
                )
            ),
            return_exceptions=True,
        )

    respuestas = asyncio.run(_simultaneas())

    inscripcion.refresh_from_db()
    assert inscripcion.cupos_asignados <= inscripcion.cupos_pagados
    assert Participacion.objects.filter(estado="ACTIVA").count() <= 1

    # Cuando el motor SERIALIZA (no bloquea), sólo una gana y la otra recibe
    # el rechazo de dominio por falta de cupo.
    exitosas = [
        respuesta for respuesta in respuestas if not isinstance(respuesta, Exception)
    ]
    if len(exitosas) == 2:
        fallidas = [
            respuesta
            for respuesta in respuestas
            if isinstance(respuesta, Exception)
        ]
        assert all(
            isinstance(respuesta, SinCuposDisponiblesError) for respuesta in fallidas
        ), fallidas
    else:
        assert exitosas, respuestas
